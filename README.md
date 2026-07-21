# Bluejay Skills

Bluejay voice/chat agent testing, evaluation, observability, and self-improvement, in Claude Code. The same skills as the Bluejay AI assistant in the app, plus the self-healing loop: point Bluejay at your agent and a test simulation and it runs the sim, diagnoses why calls fail, fixes your agent's prompt, verifies each fix, and opens a PR, looping until your target pass rate.

## Install (Claude Code)

```
/plugin marketplace add bluejay-ai-dev/bluejay-skills
/plugin install bluejay@bluejay-skills
```

Then set your API key (app.getbluejay.ai → Settings → API Keys):

```
export BLUEJAY_API_KEY=...
```

That's it — the Bluejay MCP is wired automatically by the plugin.

## Use

```
/bluejay:onboard          # first time — get to a running simulation
/bluejay:self-improve     # the test → diagnose → fix → verify loop
```

Or type `/bluejay:` in Claude Code to see the full list. Every skill runs over the Bluejay MCP that the plugin wires automatically.

## Prerequisites

- A **Bluejay account + API key** — https://getbluejay.ai
- For self-hosted **LiveKit** agents: a LiveKit Cloud project (the worker runs locally during the loop)

## What's included

Same skills as the Bluejay AI assistant in the app, now runnable from Claude Code against your own repo.

**Setup & personas**

| Skill | What it does |
|---|---|
| `/bluejay:onboard` | First-run onboarding — connect an agent, build a matching simulation, and get to a live run |
| `/bluejay:agent-onboard` | Create a brand-new agent, then smoke-test it |
| `/bluejay:new-agent-smoke-test` | Quick end-to-end health check (small sim + 3-5 sanity personas) |
| `/bluejay:persona-suite` | Turn a short brief into a diverse, runnable set of test digital humans |

**Running tests**

| Skill | What it does |
|---|---|
| `/bluejay:run-simulation` | Start a voice simulation now and report results |
| `/bluejay:sms-simulation` | Run an SMS / web-chat simulation (right queue tool per channel) |
| `/bluejay:load-test` | See how the agent holds up under many concurrent calls |
| `/bluejay:schedule-sim` | Put a simulation on a recurring schedule, or audit existing ones |
| `/bluejay:red-team-sweep` | Stress-test against hostile / manipulative callers, report vulnerabilities |

**Evals & self-improvement**

| Skill | What it does |
|---|---|
| `/bluejay:self-improve` | Multi-round test → diagnose → fix → verify loop; opens a PR with the kept fixes |
| `/bluejay:custom-metric-builder` | Turn a quality bar into well-formed pass/fail custom metrics |
| `/bluejay:agent-regression` | Re-test and verify a change didn't make the agent worse |
| `/bluejay:coverage-audit` | Find conversation branches no test currently exercises |
| `/bluejay:knowledge-gap` | Find questions the agent fumbled and what to add to its knowledge |
| `/bluejay:workflow-branch` | Add a new branch (e.g. escalation route) to an agent's workflow |

**Results & comparison**

| Skill | What it does |
|---|---|
| `/bluejay:run-report` | Actionable breakdown of one run — verdict, per-metric table, failures |
| `/bluejay:compare-runs` | Diff two runs at the metric and case level |
| `/bluejay:transcript-deep-dive` | Analyze one call in depth — exactly where and why it went wrong |
| `/bluejay:agent-scorecard` | Single health snapshot across testing and production |

**Production analysis**

| Skill | What it does |
|---|---|
| `/bluejay:production-pulse` | Quick read on live call traffic over a window |
| `/bluejay:failed-call-triage` | Rank why live calls are failing and what to fix first |
| `/bluejay:latency-triage` | Find where response time is spent and which calls are worst |
| `/bluejay:language-audit` | Language mix of calls and how well each is handled |
| `/bluejay:build-dashboard` | Design the right dashboard for an agent (widget list + link to build it) |

## Links

- Bluejay — https://getbluejay.ai
- Docs — https://docs.getbluejay.ai
