---
name: self-improve
description: Run an autonomous multi-round self-improvement loop for a voice/text agent against a Bluejay simulation. Generates pass/fail metrics from the agent's tools, runs the simulation, diagnoses failures from transcripts, fixes the system prompt, re-runs to verify each fix, and iterates until the target pass rate or cap — opening a PR with the kept fixes. Works across agent types via provider references. Use when the user asks to improve / "self-improve" a Bluejay agent against a simulation, or wires it into a cron. Safe to run headless.
---

# Bluejay Self-Improve

Closes the loop between **testing** an agent (a Bluejay Simulation) and **fixing** it (a prompt change + PR). One run = multiple rounds: run → diagnose → fix → verify → keep/revert, iterating until the target pass rate or the iteration cap.

**The loop is identical for every agent.** Only three things vary by agent type — how to check prerequisites, how to make a prompt change live, and how to run the test. Those live in a **provider reference** at `references/providers/<provider>.md`, selected by `provider` in the config. This file calls those steps; it never hardcodes them.

## Preflight (every run)
1. **Bluejay MCP connected?** (`mcp__bluejay__*` available) — else stop with the setup link.
2. **Config:** read `.bluejay/improve.yaml`. Missing → **Onboarding**. Present → load `references/providers/{provider}.md`, run its **Preflight** (fail fast with its fixes), then → **The Loop**.

## Config: `.bluejay/improve.yaml`
```yaml
provider: "livekit-local"        # selects references/providers/<this>.md
agent_id: "<bluejay agent id>"
simulation_id: "<bluejay simulation id>"
prompt_file: "<path to the system prompt the loop edits>"
success_metric_ids: []           # written by the skill at loop start
target_pass_rate: 0.9
max_iterations: 3
min_improvement: 0.05
branch_prefix: "bluejay-self-improve"
base_branch: ""                  # blank = repo default branch
# + any fields the provider reference defines (e.g. worker_cmd, livekit_agent_name)
```

## Onboarding (only when there is no config)
Rule for every input: **detect → confirm → ask only if undetectable → default.** Never ask what you can read; always confirm before creating anything in Bluejay.
1. **Provider.** Detect from the Bluejay agent's `connection_type` + repo signals; confirm. Open `references/providers/{provider}.md` and follow its **Setup** for how-to-run, prompt file, and credentials.
2. **Bluejay agent.** Reuse (`list_agents`) or register (`add_agent`).
3. **Simulation.** Reuse existing (`list_simulations`) or build one (`bulk_create_digital_humans` + `create_simulation`, `max_call_duration=5`/minutes). Ask first.
4. **Targets.** Ask `target_pass_rate` (0.9), `max_iterations` (3), `min_improvement` (0.05).
5. **Write `.bluejay/improve.yaml`.** Metrics are generated at loop start, not here.

## The Loop

### 1. Generate metrics — once, frozen for the loop (auto, no asking)
Ground "good" in what the agent is *supposed* to do — **never copied from the prompt you're fixing** (circular). Strongest signal: the agent's **tools** (a data-lookup tool ⇒ "answers from real data, not guesses"; an end-call tool ⇒ "ends when done"). Plus goals + channel best practice. Write each as a **fair, achievable** `pass_fail` metric (`create_custom_metric`); credit the outcome, not one mechanism. Reuse by name (`get_custom_metrics_by_agent`) so runs don't duplicate; attach to the sim (`update_simulation`); write ids to `success_metric_ids`. Frozen for the rest of the loop.

### 2. Baseline
Run the test via the provider reference's **Run** step → score = fraction of digital-human runs passing all metrics. Record `baseline_pass_rate`. If already ≥ `target_pass_rate`, report and exit.

### Each iteration (until a stop condition):
3. **Diagnose** — pull failing transcripts (`get_trace`); cluster into named patterns with evidence + the metric each fails. Skip patterns history already tried and reverted.
4. **Fix (0/1/many)** — one focused edit to `prompt_file` per pattern, **scoped narrowly** (an over-broad fix regresses another metric); **one commit per fix** on `{branch_prefix}/{date}`; open/append the PR.
5. **Apply + Verify** — make the change live via the provider reference's **Apply** step, then re-run the test once. **Targeted:** did each fix's metric flip to passing? **Aggregate:** pass rate held/rose, nothing else regressed.
6. **Keep or revert — per fix** — keep only if its targeted metric flipped and nothing regressed; otherwise revert that commit, re-apply, and record it in history. Update `baseline_pass_rate`.
7. **Loop or stop.**

## Stop conditions
- `baseline_pass_rate >= target_pass_rate` · `max_iterations` reached · no `min_improvement` gain for 2 rounds · no untried patterns left.

## Finalize (always)
- PR body = diagnosis log (per fix: pattern → change → kept/reverted, baseline → final). Write `.bluejay/improve-history/<date>.md`. Run the provider's teardown (e.g. stop the worker). Print PR link + final pass rate.

## Safety invariants
- A kept fix must resolve its targeted failure **and** regress no other metric.
- One commit per fix; reverts are surgical.
- Metrics frozen after step 1; edit only `prompt_file` while iterating.
- **Only ever mutate the non-production target the provider reference defines.** Prod is reached only via the PR — never an auto-push.
- Never exceed `max_iterations`. Any sim the skill creates is capped at 5-minute calls. Never merge the PR.
- On any abort, restore `prompt_file` and the target to the last known-good state. If a precondition fails, stop and report — don't guess.
