# Bluejay Skills

Skills for testing and self-improving voice/chat agents with Bluejay, across your AI coding tools.

## Install

One command wires the Bluejay MCP + these skills into every AI coding tool you have (Claude Code,
Codex, Gemini, Cursor, Windsurf, Antigravity, Claude Desktop), then runs guided onboarding:

```
npx bluejay
```

**Claude Code only**, if you'd rather install the plugin by hand:

```
/plugin marketplace add bluejay-ai-dev/bluejay-skills
/plugin install bluejay@bluejay-skills
export BLUEJAY_API_KEY=...
```

The Bluejay MCP is wired automatically by the plugin.

## Use

```
/bluejay:onboard        # first run: connect your agent, build a sim, watch it go live
/bluejay:self-improve   # close the loop: test → diagnose → fix → verify → PR
```

## Prerequisites

- A **Bluejay account + API key** — https://getbluejay.ai
- For self-hosted **LiveKit** agents: a LiveKit Cloud project (the worker runs locally during a run)

## What's included

| Skill | What it does |
|---|---|
| `/bluejay:onboard` | First-run onboarding: connect your agent, build a simulation with digital humans matching your use case, run it, and hand you the live run |
| `/bluejay:self-improve` | Multi-round test → diagnose → fix → verify loop against a Bluejay simulation; opens a PR with the kept fixes |

## Links

- Bluejay — https://getbluejay.ai
- Docs — https://docs.getbluejay.ai
