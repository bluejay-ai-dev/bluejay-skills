# Provider: retell

**Use when:** a [Retell](https://retellai.com) agent, synced into Bluejay (`connection_type == "RETELL"`, a `provider_id` matching the Retell `agent_id`, and a prompt stored on the agent's response engine). Retell agents are **hosted** — there is no local worker. Bluejay tests one by bridging a digital human to it over Retell's websocket transport, so **no phone number is required**. The loop's test target must be a **dedicated non-production agent**, never the live one; production is reached only via the PR.

**Supported response engine:** `retell-llm` (the prompt is the LLM's `general_prompt`). `conversation-flow` agents can be *read* but are **not** auto-editable by the loop (the prompt is spread across flow nodes) — improve those by hand. If the test agent is `conversation-flow`, stop and report.

**Why a separate test agent:** making a prompt change live means a real update to the Retell LLM (`general_prompt`) on the hosted agent — there is no local "dev" instance to mutate. So the loop runs against, and only ever pushes to, a **non-prod clone**. The prod agent is never touched by the loop.

**Config fields this provider adds:**
- `prod_agent_id` — the production Bluejay agent for the assistant being improved. **Read-only for the loop**; used only so the PR can name what prod should become. Never mutated.

  The top-level `agent_id` / `simulation_id` point at the **non-prod test agent** and its simulation. The loop runs, scores, and pushes against `agent_id` only. `prompt_file` is the repo file the PR edits.

## Setup (onboarding — detect → confirm → ask)
1. **Production agent.** Identify the Bluejay agent for the assistant being improved (`list_agents` → `get_agent`; confirm `connection_type == "RETELL"` and a `provider_id`). Record as `prod_agent_id`.
2. **Non-prod test agent (the loop's target).** Detect a dedicated test clone (e.g. an agent named `… [bluejay-self-improve]`, or ask). If none exists, set one up **once** (the only manual step; runs are automatic thereafter):
   - In Retell, **duplicate the prod agent** (and its LLM). Confirm it is `retell-llm`.
   - `sync_retell_agents(confirmed=True)` to import the copy as a Bluejay agent; find it via `list_agents` → `get_agent`. Confirm `connection_type == "RETELL"` and a `provider_id`. No phone number is needed (websocket transport).
   - Record its id as the top-level `agent_id`.
3. **Prompt file.** Retell prompts live in the cloud (the `retell-llm` `general_prompt`), not the repo — so establish a repo file as the reviewed source of truth. Detect an existing one; if none, export the current prompt (from `get_workflow_summary(prod_agent_id)` or the resolved `general_prompt`) into a file (e.g. `retell/<agent-name>.prompt.md`) and confirm the path. This is `prompt_file`; the PR edits it.
4. **Retell credentials.** The org's Retell **API key** must be configured in Bluejay (Settings → Integrations) — the prompt update and the test session both require it server-side. A failed push or a session that never connects (step in Run) surfaces a missing/invalid key.

## Preflight (every run)
- `agent_id` (the test agent) resolves via `get_agent` with `connection_type == "RETELL"` and a `provider_id`.
- `agent_id != prod_agent_id` — the loop must never run against or push to production.
- The agent's response engine is `retell-llm` (not `conversation-flow`); `get_workflow_summary(agent_id)` returns an editable prompt.

## Apply (make a prompt change live)
- Write the new prompt to `prompt_file`, then push it to the **test** agent only:
  1. `get_workflow_summary(agent_id)` → the node id.
  2. `update_workflow_node(agent_id, node_id, prompt=<prompt_file contents>)` — sets the new `general_prompt` Bluejay-side.
  3. `push_agent_workflow(agent_id, confirmed=True)` — updates the Retell LLM's `general_prompt` on the **test** agent. Retell reads the new prompt on the next session; no restart.
- **Never** push with `prod_agent_id`. The only path to prod is the PR.

## Run (trigger the test)
- `queue_simulation_run(simulation_id, …)` → poll `get_simulation_runs` / `get_simulation` until done → `get_simulation_results(simulation_run_id)`. Bluejay bridges each digital human to the Retell agent over the websocket transport (no phone call).
- **Dispatch / validity check:** the results must show real **agent** turns (more than one turn, nonzero agent speech). A run that COMPLETED but where the agent never spoke — caller-only transcripts, immediate silence — is an **environment failure**, not a 0% baseline: the org's Retell key is missing/invalid, or the session didn't connect. Stop and fix it (Setup steps 2 & 4); do not score the run or diagnose an agent that never answered.

## Teardown
- Nothing to stop — the agent is hosted, there is no worker. On abort, restore `prompt_file` to the last known-good and re-Apply it to the test agent so the test target matches the kept state. The prod agent was never touched, so there is nothing to roll back there.
- If the run created a throwaway test agent for this session (rather than reusing a standing one), delete it in Retell on exit.
