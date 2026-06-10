# Bluejay Skills

Self-improving voice agents, in Claude Code. Point Bluejay at your agent and a test simulation — it runs the sim, diagnoses why calls fail, fixes your agent's prompt, verifies each fix, and opens a PR, looping until your target pass rate.

## Install (Claude Code)

```
/plugin marketplace add bluejay-ai-dev/bluejay-skills
/plugin install bluejay@bluejay-skills
```

Then set your API key (Bluejay dashboard → Settings → API Keys):

```
export BLUEJAY_API_KEY=...
```

That's it — the Bluejay MCP is wired automatically by the plugin.

## Use

```
/bluejay:self-improve
```

On the first run it walks you through connecting your agent and a simulation, then starts the improvement loop.

## Prerequisites

- A **Bluejay account + API key** — https://getbluejay.ai
- For self-hosted **LiveKit** agents: a LiveKit Cloud project (the worker runs locally during the loop)

## What's included

| Skill | What it does |
|---|---|
| `/bluejay:self-improve` | Multi-round test → diagnose → fix → verify loop against a Bluejay simulation; opens a PR with the kept fixes |

## Links

- Bluejay — https://getbluejay.ai
- Docs — https://docs.getbluejay.ai
