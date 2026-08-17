---
name: self-improve-digital-humans
description: Answer whether a digital human (test case) is worth keeping, then harden it — this fixes the test, not the agent. Uses what Bluejay already knows (verdict history across runs, workflow branches, real production traffic, suite cost) to judge each test on three axes - useful (does its verdict ever change, is it redundant, does it map to real traffic or real risk), works (executes correctly and is gradeable at all), aligned (criteria mean what the user means and agree with human judgment on real transcripts). Read-only through the verdict, so it can just answer "are these tests any good / which should I delete" and stop; then optionally proposes a field-level diff, applies it on confirmation, and verifies against past calls before spending a run. Use when tests are noisy, always pass, always fail, or the user wants to audit, prune, or harden personas and success criteria.
---

# Self-improve digital humans

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

`/bluejay:self-improve` fixes the **agent**. This skill fixes the **test**. Same loop shape — evidence → diagnose → fix → verify — pointed at the digital human: its `intent`, its `success_criteria`, and the config that decides whether those can ever be reached.

**The question this skill exists to answer, bluntly: is this test worth keeping?** Everything else serves that. Bluejay already holds enough to answer it without asking the user a thing — verdict history across runs, the agent's workflow branches, the org's real production traffic, and what the suite costs to run. Answer it in those terms, name the deciding signal, and be willing to say *no*.

Every digital human gets three independent verdicts. Do not collapse them; a test can execute perfectly and still be worthless, or be a great idea that has never once run.

| Axis | Question | Fails when |
|---|---|---|
| **1. Useful** | Is this test worth keeping? | It can't discriminate (same verdict every run), duplicates another case, targets traffic that doesn't exist, or costs more attention than the signal it returns. |
| **2. Works** | Does it execute correctly in Bluejay? | Calls die before the bar, config contradicts the intent, criteria aren't gradeable from a transcript. |
| **3. Aligned** | Do the criteria mean what the user means? | Criteria grade the caller, drift from the intent, or disagree with human judgment on real calls. |

Read `references/rubric.md` before judging anything — Part D is the usefulness test (axis 1), Part A the criteria-defect taxonomy (axis 3), Part B the mechanical checklist (axis 2). This file is the procedure.

## Answer-only mode

When the user just asks whether their tests are any good — "are these test cases worth anything", "which of these should I delete", "is this test useful" — **run Steps 1–4 and stop at the report.** That's a complete answer, it's read-only, and it costs nothing. Offer the hardening pass (Steps 5–7) as the follow-on; don't assume it. A verdict of "this test is fine, delete nothing" is a legitimate and useful outcome — don't manufacture edits to look productive.

---

## Step 1 — Scope

Take the agent / simulation / digital humans from the conversation; `list_agents` → `get_simulations_by_agent` → `get_digital_humans_by_simulation` only for what's missing. `list_digital_humans` finds org-wide personas not attached to any simulation (those are axis-2 failures by definition — they never run).

Default scope is **one simulation's digital humans**. If that's more than ~15, audit the worst offenders first (most fails, most zero-turn calls, oldest) and say what you deferred — don't silently truncate.

Also pull what the suite costs to keep: `list_schedules` for how often it runs unattended, and each digital human's `num_runs`. Calls per cycle = Σ `num_runs` across the simulation; multiply by cadence. That number is what a RETIRE recommendation is worth, and it's the honest counterweight to "just leave it in, it's harmless."

## Step 2 — Read the test as authored

For each digital human, `get_digital_human` and read the whole object, not just intent. Note `intent`, `success_criteria`, `role_description`, `traits`, `journey_steps`, `speaks_first_config`, `hangup_instructions` / `hangup_phrases`, `silence_timeout`, `interruptions`, `scripted_responses`, `enriched_playback`, `expected_tool_calls`, `simulation_ids`, `num_runs`.

Also read what the agent is *supposed* to do — `get_agent`, and `get_workflow_summary(agent_id)` if it has a graph — and which custom metrics the simulation grades on (`get_custom_metrics_by_agent`). A criterion the agent has no tool, branch, or knowledge for is a bad test, not an agent bug (rubric §6).

## Step 3 — Read what actually happened (the evidence)

**Its own history.** `get_simulation_runs(simulation_id)` → for recent COMPLETED runs, `get_simulation_results(simulation_run_id)`. Per result read `status`, `duration`, and `evaluations[].goal_success` / `goal_reasoning` — that's the verdict on this digital human's `success_criteria`. Open the turn-level detail with `get_simulation_result(test_result_id)` (or `get_trace`) for anything you can't call from the reasoning alone.

Build a **verdict series per digital human across those runs**, not just a snapshot of the latest one — pass/fail/no-signal in run order. A single run tells you the current state; the series is what tells you whether the test can discriminate at all, and it's the primary input to axis 1. Go back far enough to span at least one agent change if the history allows, and say how many runs you had.

**Real callers.** The user's own production traffic is the ground truth for what a good outcome looks like from the caller's side. `list_conversations(agent_ids=[...], last="30days")` for the mix — `group_by="metric_value"` / `"ended_by"` to see how real calls actually resolve — then `get_conversation` on a handful and read them. Steal the *outcome* real callers needed, not their wording.

**Classify every past verdict** — this is the core of the skill, and it must come before any edit:

- **TRUE FAIL** — the agent genuinely fell short. The test is doing its job. Leave the criteria alone and hand the case to `/bluejay:transcript-deep-dive` or `/bluejay:self-improve`.
- **FALSE FAIL** — the agent did the right thing but the criterion is over-strict, unreachable, or the call broke first. Fix the test.
- **VACUOUS PASS** — passed without the agent doing anything meaningful (call died at the greeting, criterion unfalsifiable, criterion restates the opener). Harden the test.
- **TRUE PASS** — real. Keep.
- **NO SIGNAL** — terminal status was `NO_ANSWER`, `NO_CONNECTION`, `CALL_DROPPED`, `SYSTEM_ERROR`, `OUT_OF_FUNDS`, `CANCELLED`. Environment failure. Never score it as an agent fail or a test fail; count it separately and flag the platform issue.

Quote the deciding turn for every FALSE FAIL and VACUOUS PASS. A reclassification without a quoted turn is a guess, and editing criteria on a guess is how a real defect gets laundered into a green run.

## Step 4 — Judge the three axes

Per digital human, using the rubric:

1. **Useful** — Score the six signals in rubric Part D (discrimination, redundancy, traffic weight, risk weight, reliability, cost) and land on one of **EARNS ITS PLACE** / **WEAK** / **DEAD WEIGHT**, naming the signal that decided it. State it as a sentence a user can act on — "12 runs, 12 passes, never once flipped: this test has told you nothing since March" beats a score. Where the evidence is thin, say which signal you couldn't compute and what would settle it.
2. **Works** — Walk the mechanical checklist (rubric Part B). The commonest kills: not attached to a simulation, `enriched_playback` set (the middleware clears `intent`/`success_criteria` and switches to scripted playback), a hangup phrase that fires on the exact sentence the criterion is waiting for, and `speaks_first: false` against an agent that also waits.
3. **Aligned** — Match each clause of `success_criteria` against the eight defect patterns (Part A). Then the two-vocabulary test: `intent` describes only what the **caller** does; `success_criteria` describes only what the **agent** must do. Any sentence in the wrong column is a defect. Finally check the criteria against the *user's* stated outcome — if what they actually care about isn't in there, that gap is the finding.

Order matters: **judge usefulness first**. There's no point hardening the criteria of a test that shouldn't exist, and a WEAK verdict often turns out to be axis 2 or 3 in disguise — a test that can't discriminate because its bar is unfalsifiable is fixable, not dead.

### The report

Lead with the **suite-level answer** in two or three lines: how many tests earn their place, how much of the last run's signal was real (the true fail / false fail / vacuous pass / true pass / no signal split), what the suite costs per run, and the single biggest gap between what's tested and what production actually does.

Then one row per digital human — name | useful | works | aligned | verdict | one-line evidence — where the verdict is:

- **KEEP** — earns its place and needs nothing.
- **HARDEN** — the idea is sound, the criteria or config are not (Steps 5–7).
- **FIX CONFIG** — mechanically broken; it isn't testing anything until that's fixed.
- **RETIRE** — recommend deletion, with the reason and what's lost. Never delete anything yourself.

Sort by what a user would act on first, not alphabetically.

## Step 5 — Propose the diff (do not apply yet)

For each **HARDEN** / **FIX CONFIG** case, write the exact field-level change: field, before, after, and which classified case it's answering. Rules:

- Rewrite `success_criteria` as observable, agent-only outcomes, each clause independently failable, and failable by a call where the agent never speaks. Split compound bars into ranked clauses or promote them to real custom metrics (`/bluejay:custom-metric-builder`) when the simulation should grade them for every persona.
- If a criterion needs a fact, add the `trait` for it and reference it as `{{trait_name}}` — don't assume the caller LLM will invent a consistent account number.
- If a criterion needs a tool to fire, bind it to `expected_tool_calls` rather than hoping the agent narrates it.
- Fix the config that blocked the bar (hangup, speaks-first, silence timeout, DTMF) in the same pass — a re-worded criterion behind a premature hangup still fails.
- **Never loosen a criterion to clear a TRUE FAIL.** If the user asks for that anyway, say plainly that it hides a real defect, then do what they asked and label it in the report.
- **RETIRE** is a recommendation, never an action. Say why (duplicate of X, tests nothing the agent owns, superseded by metric Y) and let the user delete.

## Step 6 — Apply (explicit confirmation)

One `bulk_update_digital_humans` call for the whole approved set — never a loop of `update_digital_human`. Partial payload: omitted fields keep their values, but `traits`, `interruptions`, `scripted_responses`, `simulation_ids`, `journey_steps` and `hangup_phrases` **replace** the stored list, so send the full desired list for any you touch. Validate any `language`/`accent`/`gender` change against `get_voice_options` first. Report `updated_count` and per-item errors.

## Step 7 — Verify before spending a run

1. **Replay, free.** Re-judge the revised criteria against the *same* past transcripts from Step 3. Requirement in both directions: every FALSE FAIL flips to pass, every VACUOUS PASS flips to fail, and **every TRUE verdict holds**. A revision that flips a true verdict is over-corrected — revise again.
2. **Backtest custom metrics properly.** For simulation-level metrics (not the DH's own `success_criteria`), use the Metrics Lab: `create_lab(conversations=[{"test_result_id": <int>}, …], metric_ids=[…])` → `create_metric_revision` → `evaluate_conversation(metric_type="custom_metric_revision")` → poll `get_lab_detail` and compare the revision's `lab_ai_evaluations` against `human_evaluations`. Never fabricate human labels; if there are none, ask the user to annotate a few per bucket before claiming alignment.
3. **Then, and only then, a live run.** `queue_simulation_run(simulation_id, digital_human_ids=[…only the changed ones…])`. Confirm with the user first — these are real, billed calls. Never re-run a whole suite to validate a wording change. Compare with `/bluejay:agent-regression` if the same run is also meant to gauge the agent.

## Guardrails

- Read-only through Step 5. The only writes are the Step 6 bulk update, lab objects, and a confirmed run.
- This skill never edits the agent's prompt, workflow, or knowledge base. Cross to `/bluejay:self-improve` for that.
- Environment failures are never test signal and never agent signal — surface them, don't score them.
- Discover every id at runtime; never hardcode.
- If the evidence is thin (no completed runs, no production traffic), say so and grade only what you can defend — an unrun test can be judged on axes 2 and 3, never on axis 1.
