---
name: workflow-hill-climb
description: Overnight hill-climbing loop for a Bluejay agent with a multi-node workflow. Freezes a benchmark of workflow-derived test cases (every call ends with hangup-on-transfer), then iterates — diagnose failures, make one node-prompt edit, push it live, re-run the same 20–30 simulations, keep strict improvements and roll back everything else. Use when the user wants to "hill climb", "self-improve overnight", "improve the agent against its workflow without changing the test cases", or invokes /bluejay:workflow-hill-climb. Self-pacing and resumable; the user reads a trajectory report in the morning.
argument-hint: "<agent id or name> [--iterations 8] [--sims 25] [--target 0.9]"
---

# Workflow hill-climb

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell
> the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Read `DESIGN.md` in this skill's directory before the first run — it is the contract this file
executes: frozen workflow-derived benchmark, hangup-on-transfer boundary, paired scoring, one
hypothesis per iteration, push-then-verify with ledger-based rollback.

State lives in `.bluejay/hill-climb/<agent_id>/ledger.json`, written after every state change.
If a ledger exists on invocation, resume from its `phase` — never rebuild a benchmark that is
already frozen.

## Preflight
1. Resolve the agent (`list_agents` / `get_agent`). It must have a workflow
   (`get_workflow_summary` returns nodes) and a workflow-capable provider — this loop edits and
   pushes the workflow, not a repo prompt file (that's `/bluejay:self-improve`).
2. Confirm the deployment contract with the user ONCE, at launch: this loop pushes node-prompt
   edits to the live agent after every iteration and rolls back on regression. Launching the
   loop is that authorization — the overnight iterations do not re-ask, and pass
   `confirmed=true` on each push under it. If the agent serves real production traffic beyond
   the test bed, say so and make the user confirm explicitly anyway.

## Phase A — Build and freeze the benchmark (once)
1. `list_workflow_paths(agent_id)` → every distinct route to a terminal. Report the path count.
2. Generate test cases per path (`generate_digital_humans` from the workflow, or
   `bulk_create_digital_humans` with one intent per path): at least 1 DH per path, 2 for
   transfer-terminal paths, scaled to `--sims` total (default 25). Confirm the set with the user
   before creating.
3. Every DH: **hangup-on-transfer** — the caller ends the call the moment the agent initiates a
   transfer/handoff — plus a hard `max_call_duration` of 5 minutes. Non-transfer terminals end
   at their own closing line.
4. `create_simulation` + `bulk_set_digital_human_simulations`. Metrics: workflow adherence is
   native for path-derived cases; add `pass_fail` custom metrics only for what adherence can't
   see (e.g. "transfer initiated with the required context communicated"). Follow
   `/bluejay:self-improve` step-1 rules: fair, achievable, and a call where the agent never
   speaks cannot pass.
5. **Freeze.** Write DH ids, simulation id, and metric ids to the ledger with a content hash.
   From here on the benchmark is read-only; if a later phase finds it changed, abort loudly.

## Phase B — Baseline (iteration 0)
1. `queue_simulation_run`; poll `get_simulation_runs` until COMPLETED.
2. **Validity gate:** results must show the agent actually participated (real agent turns, not
   silence-timeout hangups). An environment failure is discarded and re-run once — it is never a
   0% baseline. Two consecutive environment failures → stop and report; don't diagnose an agent
   that never spoke.
3. `get_simulation_results` → record pass/fail per DH, per-path rollup. Already ≥ target →
   report and exit.

## Phase C — Iterate (1..K, default 8)
1. **Diagnose.** Pull failing transcripts (`get_simulation_result`, `get_trace`). Cluster by the
   workflow node where the run diverged. Skip clusters whose hypotheses were already rejected.
2. **One hypothesis.** Smallest node-prompt edit that plausibly fixes the largest open cluster.
   Node prompts only — never edges, never routing, never the benchmark.
3. **Edit + push.** Record each node's before-text in the ledger, `update_workflow_node`, then
   `push_agent_workflow` (under the launch authorization). Record the provider's version number
   if it returns one.
4. **Re-run.** Same simulation, same DHs. Validity gate as in Phase B.
5. **Paired compare vs the current baseline** (same DH set → per-DH flips):
   - **Accept** — net `fail→pass` minus `pass→fail` ≥ +2 AND no previously fully-passing path
     now fails: this run becomes the new baseline.
   - **Reject** — anything else, ties included: re-apply the before-text from the ledger,
     push, and mark the hypothesis rejected.
6. Ledger: iteration number, edit summary, version, score, flips, kept/rolled-back. Then next
   iteration.

**Pacing:** one iteration is one sim batch (~20–40 min for 20–30 short calls). Between queueing
and results, schedule a wake-up (10–15 min) rather than polling hot. The loop must survive a
session restart purely from the ledger.

## Stop conditions
Target reached · iteration cap · 3 consecutive rejections (local maximum — report it as such) ·
benchmark integrity violation (abort loudly) · wall-clock cap (default 8 h).

## Morning report
Lead with the verdict: baseline → final pass rate and whether the hill was climbed. Then the
trajectory table — iteration | version | edit (one line) | pass rate | net flips | kept/rolled
back — followed by what is live right now, and the failure clusters still open with a suggested
next class of edit. Include simulation run links.

## Safety invariants
- The benchmark is read-only after freeze: never regenerate, edit, or re-score old runs.
- Write surface is workflow node prompts, nothing else. No edge edits, no agent-config edits.
- Every push is reversible from the ledger alone (before-text per node per iteration).
- A kept edit strictly improved the paired score and regressed no fully-passing path.
- Never exceed the iteration or wall-clock cap. On any abort, restore the last accepted
  baseline's prompts and push, then report.
