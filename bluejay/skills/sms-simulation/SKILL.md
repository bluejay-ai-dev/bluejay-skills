---
name: sms-simulation
description: Test a text, SMS, or web-chat agent with a Bluejay simulation and report how the conversations went, using the correct queue tool for the channel. Use when the user wants to test an SMS/text/chat agent rather than a voice agent, or invokes /bluejay:sms-simulation.
---

# Run an SMS / text simulation

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: run the text-channel equivalent of a voice simulation, using the right queue tool for the channel.

## Steps

1. **Resolve the text agent + simulation.** `list_agents` / `get_simulations_by_agent`. Confirm the agent is a text/SMS agent, not voice — the queue tool differs.
2. **Check digital humans.** `get_digital_humans_by_simulation`; if empty, offer `/bluejay:persona-suite` first. For SMS, every digital human needs a valid phone number; for HTTP/chat, phone numbers may not apply.
3. **Queue the correct run:**
   - **SMS** → `queue_sms_simulation_run`
   - **HTTP / web chat** → `queue_http_text_simulation_run`
   Pass the `simulation_id`. Report the run link.
4. **Report on completion.** When `get_simulation_runs` shows COMPLETED, `get_simulation_results` and summarize: resolution rate, per-metric scores, and any conversations that stalled or hit no-reply. Use a table.

## Notes
- Picking the wrong queue tool (voice `queue_simulation_run` for a text agent) will not exercise the agent correctly — match the tool to the channel.
- If SMS runs queue but produce no artifacts, that's usually a webhook/number issue on the agent, not the simulation — flag it rather than silently reporting zero.
