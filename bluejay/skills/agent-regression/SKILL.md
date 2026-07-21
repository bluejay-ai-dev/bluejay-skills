---
name: agent-regression
description: Re-test a Bluejay agent and tell the user whether a recent change made it better, worse, or held steady versus its last completed run — with the specific cases that regressed. Use when the user wants to verify a change didn't regress an agent, run a regression check, or invokes /bluejay:agent-regression.
---

# Regression check

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: tell the user whether the agent got better, worse, or held steady versus its last run — with the specific cases that regressed.

## Steps

1. **Pick the agent + simulation.** Use the agent from the conversation; `get_simulations_by_agent` if needed. If several simulations exist and it's ambiguous, ask the user.
2. **Establish the baseline.** Call `get_simulation_runs` for the simulation and take the most recent **COMPLETED** run as the baseline. If there is no prior completed run, say so — you can still run a fresh one, but there's nothing to compare against yet.
3. **Run the new pass.** `queue_simulation_run`. Report the run link. The same digital humans run, so the comparison is apples-to-apples.
4. **Wait for completion.** If `get_simulation_runs` shows it RUNNING, tell the user you'll compare once it finishes.
5. **Compare.** When COMPLETED, call `get_simulation_results` for both the new and baseline runs and compute:
   - overall **pass rate** delta,
   - **per-custom-metric** average score delta,
   - any case that went **pass → fail** between runs.
6. **Report.** Lead with a one-line verdict: **PASS** (held or improved) or **REGRESSED** (flag the threshold, e.g. pass rate dropped >5 pts or any metric fell materially). Then a comparison table (metric | baseline | new | delta), and for each newly-failing case the persona + a transcript link so the user can see what broke.

## Notes
- Compare like with like: same simulation, same personas. If the persona set changed since the baseline, call that out — the comparison is weaker.
- Don't conclude "regressed" on noise alone; small deltas with few calls are not signal. Mention sample size.
