---
name: new-agent-smoke-test
description: Run a quick end-to-end health check on a newly built or just-changed Bluejay agent — a small simulation with 3-5 sanity personas — to confirm it can hold a basic conversation before investing in bigger test suites. Use when the user wants to smoke-test or sanity-check an agent, or invokes /bluejay:new-agent-smoke-test.
---

# Smoke-test a new agent

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: in one pass, confirm a new agent can actually hold a basic conversation and hit its core intents — before investing in bigger test suites.

## Steps

1. **Pick the agent.** Use the agent from the conversation, or `list_agents`. If it's genuinely ambiguous, ask the user.
2. **Create a small simulation** linked to the agent (`create_simulation`) — keep concurrency low; this is a sanity check, not a load test. Keep its `simulation_id`.
3. **Get a caller-ID number** via `list_phone_numbers`.
4. **Add 3–5 sanity personas** with `generate_digital_humans` (`simulation_id` set):
   - one clean **happy path** for the agent's primary intent,
   - one or two **common secondary intents**,
   - one **simple edge case** (missing info, or a polite "I changed my mind").
   Keep them easy — you're testing whether the basics work, not trying to break it (that's `/bluejay:red-team-sweep`).
5. **Queue the run** (`queue_simulation_run`) and report the run link.
6. **Report when done.** If still RUNNING, say you'll summarize on completion. When COMPLETED, `get_simulation_results` and give a short pass/fail readout per persona plus a one-line "ready for fuller testing?" verdict. If something basic failed (e.g. the agent never connected), flag it prominently — that's a config problem, not a quality nuance.

## Notes
- For SMS/text agents use `queue_sms_simulation_run` (or `queue_http_text_simulation_run`) instead of `queue_simulation_run`.
- If the agent has no phone number / connection configured, stop and tell the user — a smoke test can't run without it.
