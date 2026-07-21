---
name: agent-onboard
description: Take a brand-new Bluejay agent from "doesn't exist" to "exists and demonstrably answers a basic call" — create it with add_agent, then hand off to a smoke test. Use when the user wants to add a new agent and confirm it works, or invokes /bluejay:agent-onboard. (For first-run Bluejay setup as a whole, see /bluejay:onboard.)
---

# Onboard a new agent

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: take an agent from "doesn't exist" to "exists and demonstrably answers a basic call".

## Steps

1. **Gather what's needed** to create the agent: name, type (INBOUND/OUTBOUND), and the agent's own phone number / connection if the user provides one. Don't over-ask — take what's given.
2. **Create it.** Call `add_agent` with those details. If the user gave an explicit agent phone number, treat it as the agent's telephony number and proceed — do **not** run phone-pool tools to validate it (the pool tools are for digital-human caller IDs, not the agent's number).
3. **Confirm** the created agent (id, name, type) back to the user.
4. **Smoke-test immediately.** Hand off to the `/bluejay:new-agent-smoke-test` skill: a small simulation + 3–5 sanity personas + a queued run, so the user finds out now if the basics work.

## Notes
- If creation fails on the phone number, that's a connection/config issue — surface the exact error rather than retrying blindly.
- Stop here for quality testing — once the smoke test is green, point the user at `/bluejay:persona-suite` + `/bluejay:run-simulation` for real coverage.
