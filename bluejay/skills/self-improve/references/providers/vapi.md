# Provider: vapi

**Use when:** a [Vapi](https://vapi.ai) voice assistant, synced into Bluejay (`provider == "VAPI"`, a `vapi_assistant_id`, and a system prompt stored in the assistant's `model`). Vapi assistants are **hosted** — there is no local worker, and Bluejay tests one by placing a real phone call to it. So the loop's test target must be a **dedicated non-production assistant**, never the live one. Production is reached only via the PR; merging it (and pushing that prompt to the prod assistant) is a human step.

**Why a separate test assistant:** making a prompt change live on Vapi means a real `PATCH /assistant/{id}` (via `push_agent_workflow` → the live assistant). There is no local "dev" instance to mutate instead. So the loop runs against, and only ever pushes to, a **non-prod clone** of the assistant. The prod assistant is never touched by the loop.

**Config fields this provider adds:**
- `prod_agent_id` — the production Bluejay agent (the assistant you actually want to improve). **Read-only for the loop** — used only so the PR can name what prod should become. Never mutated.

  The top-level `agent_id` / `simulation_id` point at the **non-prod test assistant** and its simulation. The loop runs, scores, and pushes against `agent_id` only. `prompt_file` is the repo file the PR edits (the reviewed source of truth for the prod prompt).

## Setup (onboarding — detect → confirm → ask)
1. **Production assistant.** Identify the Bluejay agent for the assistant being improved (`list_agents` → `get_agent`; confirm `provider == "VAPI"` and a `vapi_assistant_id`). Record as `prod_agent_id`.
2. **Non-prod test assistant (the loop's target).** Detect a dedicated test clone (e.g. an agent named `… [bluejay-self-improve]`, or ask). If none exists, set one up **once** (this is the only manual step; runs are automatic thereafter):
   - In Vapi, **duplicate the prod assistant** and attach a **phone number** to the copy (Bluejay dials the assistant at its number — without one it can't be called).
   - `sync_vapi_agents(confirmed=True)` to import the copy as a Bluejay agent; find it via `list_agents` → `get_agent`. Confirm `provider == "VAPI"`, a `vapi_assistant_id`, and a non-null `phone_number`.
   - Record its id as the top-level `agent_id`.
3. **Prompt file.** Vapi prompts live in the cloud, not the repo — so establish a repo file as the reviewed source of truth. Detect an existing one; if none, export the current system prompt (from `get_workflow_summary(prod_agent_id)` → the node's prompt, or the stored `workflow.model.messages[role==system].content`) into a file (e.g. `vapi/<assistant-name>.prompt.md`) and confirm the path. This is `prompt_file`; the PR edits it.
4. **Vapi credentials.** The org's Vapi **private API key** must be configured in Bluejay (Settings → Integrations) — `push_agent_workflow` and the test call both require it server-side. It is not set here; a failed push or a call that never connects (step in Run) surfaces a missing/invalid key.

## Preflight (every run)
- `agent_id` (the test assistant) resolves via `get_agent` with `provider == "VAPI"`, a `vapi_assistant_id`, and a non-null `phone_number`.
- `agent_id != prod_agent_id` — the loop must never run against or push to production.
- `get_workflow_summary(agent_id)` returns a node whose prompt the loop can edit (a standalone assistant = one node).

## Apply (make a prompt change live)
- Write the new prompt to `prompt_file`, then push it to the **test** assistant only:
  1. `get_workflow_summary(agent_id)` → the node id.
  2. `update_workflow_node(agent_id, node_id, prompt=<prompt_file contents>)` — writes Bluejay-side only.
  3. `push_agent_workflow(agent_id, confirmed=True)` — does the real `PATCH /assistant/{vapi_assistant_id}` on the **test** assistant. Vapi reads the new prompt on the next call, so the change is live immediately; no restart.
- **Never** call `push_agent_workflow` with `prod_agent_id`. The only path to prod is the PR.

## Run (trigger the test)
- `queue_simulation_run(simulation_id, …)` → poll `get_simulation_runs` / `get_simulation` until done → `get_simulation_results(simulation_run_id)`. Bluejay places a real call: `POST https://api.vapi.ai/call/phone` with the test assistant's `assistantId` + `phoneNumberId`, dialing each digital human.
- **Dispatch / validity check:** the results must show real **agent** turns (more than one turn, nonzero agent speech). A run that COMPLETED but where the assistant never spoke — caller-only transcripts, immediate hangup — is an **environment failure**, not a 0% baseline: the assistant has no phone number, the org's Vapi key is missing/invalid, or the call didn't connect. Stop and fix it (see Setup steps 2 & 4); do not score the run or diagnose an assistant that never answered.

## Teardown
- Nothing to stop — the assistant is hosted, there is no worker. On abort, restore `prompt_file` to the last known-good and re-Apply it to the test assistant so the test target matches the kept state. The prod assistant was never touched, so there is nothing to roll back there.
- If the run created a throwaway test assistant for this session (rather than reusing a standing one), delete it in Vapi on exit.
