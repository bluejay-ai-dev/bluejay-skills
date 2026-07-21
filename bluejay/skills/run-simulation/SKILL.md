---
name: run-simulation
description: Start a Bluejay simulation against a voice agent right now and report the results. Resolves the agent and simulation, checks it has digital humans, queues the run, and gives a pass-rate readout when it completes. Use when the user wants to test an agent now, "run a sim", or invokes /bluejay:run-simulation. For SMS/text agents use /bluejay:sms-simulation instead.
---

# Run a simulation

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: get a simulation running against an agent with the fewest questions, then report results.

## Steps

1. **Resolve the agent + simulation.** Use the agent from the conversation if one is already in play. `get_simulations_by_agent` to list candidates. If there's exactly one obvious target, proceed; if genuinely ambiguous, ask the user.
2. **Confirm there are digital humans.** Call `get_digital_humans_by_simulation`. If none are linked, stop and offer the `/bluejay:persona-suite` skill (a run with no personas does nothing).
3. **Queue it.** Call `queue_simulation_run` with the `simulation_id`. Report the run link `https://app.getbluejay.ai/simulations/{simulationId}/runs/{runId}` and that it is queued/running.
4. **Report on completion.** Runs take minutes. If `get_simulation_runs` shows RUNNING, say you'll summarize when it finishes (the user can ask "show the run results"). When COMPLETED, call `get_simulation_results` and give a short pass-rate + per-metric readout as a table.

## Notes
- For SMS/text agents, use the `/bluejay:sms-simulation` skill (different queue tool).
- Do not edit digital-human goals right before running — set them when the personas are created.
