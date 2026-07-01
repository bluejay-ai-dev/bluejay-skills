# Provider: elevenlabs

**Use when:** an [ElevenLabs](https://elevenlabs.io) Conversational AI (Convai) agent, synced into Bluejay (`provider == "ELEVENLABS"` / `connection_type == "ELEVEN_LABS"`, an `eleven_labs_agent_id`, and a system prompt stored on the agent). ElevenLabs Convai agents are **hosted** — there is no local worker. Bluejay tests one by opening a Convai session and bridging a digital human to it over ElevenLabs' websocket transport, so **no phone number is required** (unlike a PSTN agent). The loop's test target must be a **dedicated non-production agent**, never the live one; production is reached only via the PR.

**Why a separate test agent:** making a prompt change live means a real `PATCH /v1/convai/agents/{id}` on the hosted agent — there is no local "dev" instance to mutate. So the loop runs against, and only ever pushes to, a **non-prod clone**. The prod agent is never touched by the loop.

**Config fields this provider adds:**
- `prod_agent_id` — the production Bluejay agent for the assistant being improved. **Read-only for the loop**; used only so the PR can name what prod should become. Never mutated.

  The top-level `agent_id` / `simulation_id` point at the **non-prod test agent** and its simulation. The loop runs, scores, and pushes against `agent_id` only. `prompt_file` is the repo file the PR edits (the reviewed source of truth).

## Setup (onboarding — detect → confirm → ask)
1. **Production agent.** Identify the Bluejay agent for the assistant being improved (`list_agents` → `get_agent`; confirm `connection_type == "ELEVEN_LABS"` and an `eleven_labs_agent_id`). Record as `prod_agent_id`.
2. **Non-prod test agent (the loop's target).** Detect a dedicated test clone (e.g. an agent named `… [bluejay-self-improve]`, or ask). If none exists, set one up **once** (the only manual step; runs are automatic thereafter):
   - In ElevenLabs, **duplicate the prod Convai agent**.
   - `sync_elevenlabs_agents(confirmed=True)` to import the copy as a Bluejay agent; find it via `list_agents` → `get_agent`. Confirm `connection_type == "ELEVEN_LABS"` and an `eleven_labs_agent_id`. No phone number is needed (websocket transport).
   - Record its id as the top-level `agent_id`.
3. **Prompt file.** ElevenLabs prompts live in the cloud at `conversation_config.agent.prompt.prompt`, not the repo — so establish a repo file as the reviewed source of truth. Detect an existing one; if none, export the current system prompt (from `get_workflow_summary(prod_agent_id)` or the stored agent payload's `conversation_config.agent.prompt.prompt`) into a file (e.g. `elevenlabs/<agent-name>.prompt.md`) and confirm the path. This is `prompt_file`; the PR edits it.
4. **ElevenLabs credentials.** The org's ElevenLabs **API key** (`xi-api-key`) must be configured in Bluejay (Settings → Integrations) — the prompt PATCH and the test session both require it server-side. A failed push or a session that never connects (step in Run) surfaces a missing/invalid key.

## Preflight (every run)
- `agent_id` (the test agent) resolves via `get_agent` with `connection_type == "ELEVEN_LABS"` and an `eleven_labs_agent_id`.
- `agent_id != prod_agent_id` — the loop must never run against or push to production.
- `get_workflow_summary(agent_id)` returns a node whose prompt the loop can edit (a standalone Convai agent = one node).

## Apply (make a prompt change live)
- Write the new prompt to `prompt_file`, then push it to the **test** agent only:
  1. `get_workflow_summary(agent_id)` → the node id.
  2. `update_workflow_node(agent_id, node_id, prompt=<prompt_file contents>)` — writes the prompt at `conversation_config.agent.prompt.prompt` on the Bluejay side.
  3. `push_agent_workflow(agent_id, confirmed=True)` — does the real `PATCH /v1/convai/agents/{eleven_labs_agent_id}`. ElevenLabs reads the new prompt on the next session, so the change is live immediately; no restart.
- **Never** call `push_agent_workflow` with `prod_agent_id`. The only path to prod is the PR.

## Run (trigger the test)
- `queue_simulation_run(simulation_id, …)` → poll `get_simulation_runs` / `get_simulation` until done → `get_simulation_results(simulation_run_id)`. Bluejay opens an ElevenLabs Convai session and bridges each digital human to it over the websocket transport (no phone call).
- **Dispatch / validity check:** the results must show real **agent** turns (more than one turn, nonzero agent speech). A run that COMPLETED but where the agent never spoke — caller-only transcripts, immediate silence — is an **environment failure**, not a 0% baseline: the org's ElevenLabs key is missing/invalid, or the session didn't connect. Stop and fix it (Setup steps 2 & 4); do not score the run or diagnose an agent that never answered.

## Teardown
- Nothing to stop — the agent is hosted, there is no worker. On abort, restore `prompt_file` to the last known-good and re-Apply it to the test agent so the test target matches the kept state. The prod agent was never touched, so there is nothing to roll back there.
- If the run created a throwaway test agent for this session (rather than reusing a standing one), delete it in ElevenLabs on exit.
