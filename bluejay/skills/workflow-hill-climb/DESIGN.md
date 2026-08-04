# Workflow hill-climb — how the self-improvement actually works

One paragraph: freeze a benchmark derived from the agent's own workflow graph, then improve the
agent against it in small attributable steps — deploy each step live, re-measure on the identical
benchmark, keep only strict improvements, roll everything else back. Run it overnight for K
iterations and read the trajectory in the morning. The benchmark never moves; only the agent does.
That is the whole trick: with a fixed instrument, "the first run is worse than the last run"
becomes a measurement, not a hope.

## Why the benchmark is workflow-derived

`list_workflow_paths` enumerates every distinct route from the workflow's start to each terminal
outcome. Each path becomes one or more test cases (digital humans) whose intent drives the
conversation down exactly that route. Coverage is therefore the graph itself: "better" means
better at the thing the workflow defines, per branch, not better at a hand-picked anecdote. A
path that never had a test case is a branch the loop cannot regress unnoticed — so every path
gets at least one.

## Why the benchmark is frozen

If test cases regenerate between iterations, scores are incomparable and the hill disappears —
you can "improve" forever by wobbling the yardstick. So generation happens exactly once. The
digital-human ids, simulation id, and metric ids are recorded in the ledger at freeze time, and
every later phase treats them as read-only. The loop's only write surface is the agent's workflow
node prompts. If the benchmark is found modified mid-run (id set changed, DH edited), the run
aborts loudly instead of reporting a number that means nothing.

## Why every call ends with hangup-on-transfer

Transfer (or handoff/merge) is the terminal success boundary for these agents. A simulation
cannot complete a real transfer — there is no genuine second leg to receive it — so anything
graded past the moment of transfer initiation measures the harness, not the agent. Therefore:

- Every digital human is configured to hang up the moment the agent initiates a transfer.
- The pass criterion is everything up to that boundary: reached the correct terminal, via the
  correct route, having collected/communicated what the path requires.
- Paths whose terminal is not a transfer (voicemail, not-interested, wrong-number, invalid
  number) end at their own terminal line and are graded the same way.

This also bounds call duration, which is what makes 20–30 calls per iteration cheap enough to
run eight times a night.

## Scoring: paired, per-path, noise-aware

Simulated conversations are stochastic; a naive pass-rate delta will accept noise. The same
digital humans run every iteration, so score changes pair per test case:

- For each DH, compare this iteration's outcome to the current baseline's: `fail→pass` and
  `pass→fail` flips.
- **Accept rule (strict hill climb):** net flips ≥ +2 AND no path cluster that was fully passing
  becomes failing. Anything weaker — including a tie — is a reject; the baseline stands.
- Record per iteration: pass rate, per-path breakdown, and the named flip lists, so the morning
  report shows *which* behaviors moved, not just a number.

The harness-stability assumption is explicit: Bluejay is the fixed instrument. A run where the
agent never actually joined (no agent turns, silence hangups, connection errors) is an
environment failure, not a score — the validity gate discards it and the iteration re-runs
rather than polluting the trajectory.

## The improve step: one hypothesis per iteration

Failures cluster by workflow node — adherence results name the node or edge where each run
diverged. Each iteration:

1. Take the largest failure cluster not already tried-and-rejected.
2. Form ONE minimal hypothesis: the smallest node-prompt edit that plausibly fixes that cluster.
3. Edit only the implicated node(s). Never edit edges or routing in this loop — edge semantics
   are provider-lossy on some providers, and a routing change confounds attribution across every
   path at once.

One hypothesis per iteration is what makes accept/reject meaningful: when the score moves, you
know which edit moved it.

## Deploy and rollback

- Deploy: `update_workflow_node` (Bluejay-side edit) → `push_agent_workflow` (live). On
  versioned providers (Bland, DFCX) each push snapshots a version — record its number in the
  ledger as the iteration's deploy artifact.
- Rollback never depends on the provider: the ledger stores the exact before/after prompt text
  for every edited node, every iteration. A reject re-applies the before-text and pushes. The
  provider's version history is the audit trail; the ledger is the mechanism.

Pushing live after each turn is the point — the benchmark exercises the deployed agent, so
"tested" always means "tested what is actually serving." The rollback path is what makes that
safe.

## The overnight loop

- **Iteration 0 (baseline):** run all N sims, validity-gate, record. If already at target, stop.
- **Iterations 1..K (default 8):** diagnose → one-hypothesis edit → push → run N sims → paired
  compare → accept (new baseline) or rollback.
- One iteration ≈ one sim batch: queue → calls run → evaluations settle (typically 20–40 minutes
  for 20–30 short calls). The skill self-paces with scheduled wake-ups and persists the ledger
  after every state change, so a dead session resumes exactly where it stopped.
- **Morning report:** trajectory table (iteration | deploy artifact | edit summary | pass rate |
  net flips | kept/rolled back), what is live right now, and the failure clusters still open.

## Stop conditions

Target pass rate reached · iteration cap · three consecutive rejections (a local maximum — needs
a human or a different class of edit) · benchmark integrity violated (abort loudly) · wall-clock
cap.

## Invariants

1. Benchmark (digital humans, simulation, metrics) is read-only after freeze. The write surface
   is workflow node prompts, nothing else.
2. Every deploy is recorded in the ledger and reversible from the ledger alone.
3. A kept edit strictly improved the paired score and regressed no fully-passing path.
4. Improvement claims come only from the frozen benchmark — never from regenerated or
   hand-picked cases.
