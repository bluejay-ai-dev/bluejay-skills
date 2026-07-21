---
name: agent-scorecard
description: Produce a single health snapshot of a Bluejay agent across both testing (simulation pass rate + trend, weakest metrics) and production (call volume, status mix, failure rate), with the top things to fix. Use when the user wants an overall health read on an agent, a scorecard, or invokes /bluejay:agent-scorecard.
---

# Agent scorecard

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: one screen that tells the user how an agent is doing overall and what to do next.

## Steps

1. **Resolve the agent.** `list_agents` / the agent from the conversation.
2. **Testing side.** `get_simulations_by_agent` → for the most recent runs, `get_simulation_runs` + `get_simulation_results`: latest pass rate and the trend across the last few runs, plus the weakest custom metrics.
3. **Production side.** `list_call_logs` (default last 24h, or the user's range): call volume, status mix, and failure rate (use the response's `total` for counts).
4. **Assemble the scorecard:**
   - headline grade / pass rate,
   - testing trend (improving / flat / regressing),
   - production volume + failure rate,
   - **top 3 things to fix**, each pointing at the skill that addresses it (`/bluejay:failed-call-triage`, `/bluejay:agent-regression`, `/bluejay:coverage-audit`, …).

## Notes
- Keep it scannable — tables and one-liners, no walls of text.
- If production call logs aren't available for this org, say so and base the scorecard on simulation data alone rather than inventing numbers.
