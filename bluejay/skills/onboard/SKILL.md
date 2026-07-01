---
name: onboard
description: First-run onboarding for Bluejay. Walks the user through creating and running their very first simulation entirely over the Bluejay MCP — connect (or register) their voice/chat agent, build a simulation whose digital humans match their real use case, queue the run, and hand them the live run link. Ends as soon as the run is going; does not diagnose or fix. Use when a user is new to Bluejay, asks to "get started", "set up my first simulation", or is dropped here by `npx bluejay`. Safe and read-mostly until the user confirms each create.
---

# Bluejay Onboard

Get a new user from nothing to a **running simulation** in one guided pass, all via `mcp__bluejay__*`.
The finish line is the **live run** — connect the agent → build a matching simulation → run it → link them to it.
No diagnosis, no fixing (that's `/bluejay:self-improve` later).

**Rule for every input: detect → confirm → ask only if undetectable → default. Never ask what you can read; always confirm before creating anything in Bluejay.**

## Preflight
1. **MCP connected?** `mcp__bluejay__*` tools available — if not, stop: the user needs to finish `npx bluejay` / set `BLUEJAY_API_KEY`, then reopen.
2. **Greet briefly.** One line on what's about to happen (4 steps, ~2 min, ends at a live run). Then go.

## 1 · Connect the agent
The thing being tested is the user's voice/chat agent.
1. **Reuse or register.** `list_agents`. If one obviously matches their repo/use case, confirm and use it. Otherwise `add_agent` (its `knowledge_base` field takes a free-form name string like "My Agent KB" — no pre-existing KB object needed).
2. **Provider / how it's reached.** Detect from the agent's `connection_type` + repo signals; confirm. For a phone/hosted agent, Bluejay dials it directly — nothing to run locally. For a **self-hosted LiveKit** agent, the local worker must be running during the sim — open `../self-improve/references/providers/livekit-local.md` and follow its **Setup** (credentials, run command) before step 3.

## 2 · Build the simulation (digital humans that match their use case)
1. **Infer the use case.** Read the agent's prompt, tools, and goals to describe who calls it and why (e.g. "borrowers asking about payoff amounts", "patients rescheduling appointments"). State it back in one sentence and confirm.
2. **Generate matching digital humans.** `generate_digital_humans` from that use case (or hand-author 2–3 with `bulk_create_digital_humans`). Aim for a small, realistic spread — a couple of common callers plus one edge case. Show the list; let the user tweak before committing.
3. **Create the simulation.** `create_simulation` with those digital humans. **Cap calls: `max_call_duration=5` (minutes).** Confirm the name.

## 3 · Run it
`queue_simulation_run(simulation_id, …)` (pass the `livekit_agent_name` too for the livekit-local provider). Confirm it's queued/accepted.

## 4 · Hand off to the live run
As soon as the run is queued/running, **give the user the link and stop** — don't poll to completion.
- Use a run URL the MCP returns if present; otherwise build it from the ids and point at the dashboard: `https://app.getbluejay.ai` → the simulation → this run.
- One-line recap: agent connected, N digital humans matching "<use case>", run live at <link>.
- Point to next steps: watch the run finish in the dashboard; when you want to close the loop on failures, run `/bluejay:self-improve`.

## Safety invariants
- Confirm before every create (`add_agent`, `bulk_create_digital_humans`, `create_simulation`) and before `queue_simulation_run`.
- Any simulation created here is capped at 5-minute calls.
- Never mutate the user's production agent; onboarding only reads it to infer the use case.
- If a precondition fails (no MCP, agent unreachable, livekit creds missing), stop and report the fix — don't guess or fabricate ids.
