---
name: run-report
description: Turn a Bluejay simulation run's raw results into an actionable report — verdict, per-metric table, and the failing calls with transcript links. Use when the user wants to understand how one run did in detail, "report on a run", or invokes /bluejay:run-report. For two-run comparisons use /bluejay:compare-runs; for regression checks use /bluejay:agent-regression.
---

# Report on a simulation run

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: turn a run's raw results into a report a human can act on in 30 seconds.

## Steps

1. **Identify the run.** Use the run from the conversation if one is selected. Otherwise `get_simulations_by_agent` → `get_simulation_runs` and pick the run the user means (most recent COMPLETED if unspecified).
2. **Pull results.** `get_simulation_results` for the run.
3. **Summarize top-down:**
   - **Verdict** — one line ("38/40 passed; two failed identity verification").
   - **Per-metric table** — metric | pass rate | avg score.
   - **Failures** — list the failing calls with persona + the specific metric that failed + a transcript link, so the user can jump straight to the problem.

## Notes
- Be honest about sample size — a 100% pass rate on 3 calls is not a green light.
- Don't fabricate recording/S3 URLs; link to the in-app run/result pages instead (`https://app.getbluejay.ai/simulations/...`).
- For two-run comparisons use `/bluejay:compare-runs`; for "is this worse than before" use `/bluejay:agent-regression`.
