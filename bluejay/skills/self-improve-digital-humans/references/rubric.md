# Rubric — usefulness (axis 1), mechanical checks (axis 2), criteria defects (axis 3)

Used by `/bluejay:self-improve-digital-humans`. Every finding must cite either a config field, a platform number, or a quoted turn from a real transcript.

- **Part A** — the eight ways success criteria go wrong (axis 3)
- **Part B** — mechanical checklist (axis 2)
- **Part C** — statuses that are never signal
- **Part D** — is this test useful? (axis 1 — the crux)

---

## Part A — The eight ways success criteria go wrong

### 1. Wrong subject — grades the caller
`success_criteria` is the **agent's** bar. Any clause whose subject is the caller is unscoreable noise, because the caller is Bluejay's own digital human and always complies.

> ✗ "The caller provides their date of birth and confirms the appointment."
> ✓ "The agent asks for the caller's date of birth, verifies it against the record, and states the confirmed appointment date and time back."

Move the caller half into `intent`, which describes only what the caller says or does. Keep the two vocabularies disjoint — this single split fixes more broken tests than any other change.

### 2. Unreachable — the caller never supplies the trigger
The criterion waits for something the persona is never driven to produce: a policy number that has no `trait`, an escalation the `intent` never asks for, a step 2 that only exists in `journey_steps` the caller never reaches. The agent cannot pass a bar the conversation never approaches.

Fix: add the `trait` (typed, and referenced as `{{trait_name}}` inside `intent`), extend the intent to actually pursue it, or delete the clause. Prefer deleting over inventing new caller behavior the user didn't ask for.

### 3. Self-defeating — the call ends before the bar
The digital human's own exit config kills the call at the moment of truth. Classics:

- `hangup_phrases` containing a phrase that matches the agent's hand-off announcement ("let me transfer you", "please hold") — the caller hangs up on the very sentence the criterion is waiting for.
- `hangup_instructions` that fire on the first plausible answer, while the criterion also requires a confirmation or a callback commitment.
- `silence_timeout` shorter than the agent's real tool latency (lookups, transfers, IVR waits).
- `interruptions: high` against an agent whose compliance disclosure is the graded artifact — the caller talks over the thing being scored.

Symptom in the data: a cluster of fails at suspiciously uniform low `num_turns` / short `duration`, right after the same agent utterance.

### 4. Unfalsifiable — no transcript could fail it
"The agent is helpful and professional." "The agent handles the call appropriately." These grade the judge's mood.

Hard test: **could a call where the agent never spoke at all pass this criterion?** If yes, it's broken. Every clause must name an observable — a specific fact stated, a specific action taken, a specific commitment made.

### 5. Compound — several bars welded into one string
Four requirements in one `success_criteria` means a call that meets three grades arbitrarily, and the `goal_reasoning` can't tell you which one broke.

Fix: keep the criteria to the outcomes that define *this* persona's call, ranked, and promote anything that should hold for **every** persona into a simulation-level custom metric instead (`/bluejay:custom-metric-builder`). Per-persona criteria and cross-cutting metrics are different tools; don't duplicate a metric inside criteria.

### 6. Out of scope — grades what the agent doesn't own
The criterion requires a capability the agent has no tool, workflow branch, or knowledge-base entry for. The test will fail forever and the fail says nothing about quality.

This is a finding, not a fix: report it as a **product/coverage** question ("do you want the agent to be able to do this?"). If yes, it belongs in the roadmap and the test can stay, flagged as expected-fail. If no, the criterion goes.

### 7. Un-gradeable from the transcript
The judge sees the transcript and the tool calls. Nothing else. "The CRM record was updated", "the callback was actually scheduled", "the correct queue received the transfer" are invisible to it.

Fix: bind the criterion to observable evidence — the tool call (`expected_tool_calls`, with `name` and, when it matters, `parameters`) plus what the agent says. Grade the observable proxy, and say in the criterion that that's what you're grading.

### 8. Drifted — written against an older agent
The criterion encodes a script, phrasing, or flow the agent no longer uses; production transcripts show real calls resolving a different way. The test now fails good behavior.

Fix: re-anchor on the outcome the caller needs, not the path the old prompt took. Outcome-shaped criteria survive prompt changes; phrase-matching criteria don't.

---

## Part B — Mechanical checklist (does it actually run?)

Config-level. Each of these silently voids the test.

| Check | Broken when | Fix |
|---|---|---|
| Attached to a simulation | `simulation_ids` empty | Add it (`simulation_ids` **replaces** the list — send the full set) |
| Not in scripted-playback mode | `enriched_playback` or `formatted_transcript` set | Those clear `intent`/`success_criteria` and switch the runtime to deterministic playback. An intent-driven, criteria-graded test cannot have them |
| Someone opens the call | `speaks_first_config.speaks_first: false` against an agent that also waits | Set `{speaks_first: true, mode: "ai_generated"}`, or a `custom` message for a fixed opener |
| Exit config permits the bar | see defect §3 | Loosen `hangup_phrases` / `hangup_instructions`, raise `silence_timeout` (min 15s) |
| Latency headroom | agent does slow lookups | Raise `endpointing_delay` / `silence_timeout` above real tool latency |
| Menu navigation | agent front-ends an IVR | `default_dtmf_or_voiced: "dtmf"`, `extension` when a direct extension is needed, `allow_dtmf_tool` on |
| Voice combo valid | non-default `language`/`accent`/`gender` | Validate with `get_voice_options` before writing |
| Facts are typed data | numbers or dates buried in prose | Move them into `traits` with the right `trait_data_type`; reference via `{{trait_name}}` |
| Dynamic, not pinned | `scripted_responses` used to fake a persona | Scripted responses bypass the caller LLM and make the test brittle. Keep them for deliberate verbatim lines and DTMF only |
| Enough runs to mean anything | `num_runs: 1` on a bar that's ever been flaky | Raise it, or stop reading single-run flips as regressions |
| Distinct from its neighbours | two personas with the same intent and bar | Duplicate cost, no extra coverage — recommend retiring one |

## Part C — Statuses that are never signal

`NO_ANSWER`, `NO_CONNECTION`, `CALL_DROPPED`, `SYSTEM_ERROR`, `OUT_OF_FUNDS`, `CANCELLED` are terminal **environment** failures. A run full of these is not a 0% agent score and not a bad test — it's a platform problem. Count them separately, report them, and exclude them from every pass rate you quote.

`COMPLETED` is the only terminal success status. In-flight (`QUEUED`, `RUNNING`, `EVALUATING`, …) means the evidence isn't in yet — wait rather than scoring a partial run.

---

## Part D — Is this test useful?

The crux. A test earns its place by **changing what someone would do**. It does that only if its verdict is uncertain before the run, informative after it, and attached to something that matters. Bluejay already holds every signal needed to decide — none of this requires asking the user.

### The six signals

**1. Discrimination — can its verdict ever change?** *The single strongest signal; weight it above the rest.*
From the verdict series across runs. A test whose result is a foregone conclusion carries no information no matter how well written it is.

| Pattern | Reading |
|---|---|
| Passes every run, never flipped | Tells you nothing. Either the bar is below the agent's floor, or it's unfalsifiable (Part A §4). Harden the bar or retire. |
| Fails every run | Informative exactly once. If the underlying defect is known and unfixed, the test is now a standing reminder, not a test — track it as an issue and stop paying to re-discover it. If nobody can say *why* it fails, it's probably broken (Part A §2, §3, §6). |
| Flips with agent changes | **Maximum value.** This is a real regression detector — protect it. |
| Flips with no agent change | Noise, not signal. Either genuine agent nondeterminism worth its own investigation, or a flaky bar. Raise `num_runs` before concluding. |
| Never run | Unknown. Judge axes 2 and 3, say axis 1 is unanswerable, and recommend one run to find out. |

**2. Redundancy — does something else already cover this?**
Two digital humans with the same intent hitting the same `get_workflow_summary` branch with the same bar are one test and one recurring bill. Same for a `success_criteria` clause that restates a simulation-level custom metric already scoring every call — the metric covers it for the whole suite, so the clause is duplicated work with a second chance to disagree. Check personas against each other, then against the metric set.

**3. Traffic weight — do real callers do this?**
`list_conversations(agent_ids=[…], last="30days")`, grouped by metric value, label, or metadata, gives the real distribution. Compare the persona set to it. Two distinct findings fall out, and both are worth reporting:
- a test for an intent that barely appears in real traffic (low value — unless signal 4 rescues it), and
- a high-volume real intent with **no** test at all (the more valuable finding; hand to `/bluejay:coverage-audit`).

Weight it by where production actually *fails*, not just call count: an intent that real callers hit constantly and the agent always handles is a weaker test target than the one that goes wrong every week.

**4. Risk weight — what does failure cost?**
Volume alone does not decide. A rare call that ends in a missed compliance disclosure, a failed transfer on an emergency, a mishandled payment, or leaked PII outranks a common call about opening hours. Low traffic plus high consequence is a **keep** — say so explicitly so nobody prunes it on volume next quarter. This is the one signal where you should ask the user if it's genuinely unclear; everything else, infer.

**5. Reliability — how much of its output is real signal?**
Share of runs ending in Part C environment statuses, plus the false-verdict rate from the Step 3 classification. A test that returns `NO_ANSWER` half the time, or whose fails are mostly false, is spending human attention to produce noise. That's a cost, not a neutral.

**6. Cost — what does keeping it charge you?**
`num_runs` × schedule cadence = billed calls per month, per test. Real money and real minutes. Cheap tests can be kept on a hunch; a `num_runs: 5` persona on a nightly schedule that has never once flipped is an easy, quantifiable delete.

### Deciding

- **EARNS ITS PLACE** — discriminates (or is genuinely new), non-redundant, and attached to real traffic or real risk.
- **WEAK** — the idea is right but a signal is failing: can't discriminate, mostly noise, or overlaps another test. Usually fixable — check Parts A and B before recommending anything drastic, because "always passes" is very often an unfalsifiable bar rather than a worthless test.
- **DEAD WEIGHT** — no discrimination, no unique coverage, no risk case, and it costs money every cycle. Recommend RETIRE with the number attached.

Two standing rules:

- **Never claim a test is useless on missing evidence.** No runs, no production traffic, or a suite younger than one agent change means you cannot compute signal 1 — say which signal you're missing and what would settle it. "I can't tell yet, run it once" is an honest answer; a confident RETIRE on zero data is not.
- **A test that fails for a real reason is a good test.** The whole point of axis 1 is to find tests that tell you nothing — not to prune the ones telling you something you'd rather not hear.
