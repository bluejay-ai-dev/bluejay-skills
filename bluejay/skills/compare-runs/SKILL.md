---
name: compare-runs
description: Compare two Bluejay simulation runs to show exactly what changed — at the metric level and the case level (which cases flipped pass→fail and fail→pass). Use when the user wants to compare any two runs (e.g. before/after a prompt change), or invokes /bluejay:compare-runs. For an automatic "did my latest change regress?" verdict use /bluejay:agent-regression.
---

# Compare two runs

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: show exactly what changed between two chosen runs, at the metric level and the case level.

## Steps

1. **Identify both runs.** The user may name them, or you infer from `get_simulation_runs` (e.g. "before and after my prompt change" → the two most recent COMPLETED). If which-two is ambiguous, ask the user.
2. **Pull results for each** via `get_simulation_results`.
3. **Diff at two levels:**
   - **Metric level** — table of metric | run A | run B | delta.
   - **Case level** — list cases that flipped pass→fail (regressions) and fail→pass (fixes), each with persona + transcript links.
4. **Verdict.** One line on whether B is better, worse, or mixed, and the single biggest driver of the difference.

## Notes
- Only compare like with like: same simulation / persona set. If the personas differ between the two runs, say so — the diff is then suggestive, not conclusive.
- For an automatic "did my latest change regress?" check with a verdict, use `/bluejay:agent-regression` instead.
