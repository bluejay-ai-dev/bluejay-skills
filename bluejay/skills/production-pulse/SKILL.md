---
name: production-pulse
description: Give a fast, accurate read on live Bluejay production call traffic over a window — volume, inbound vs outbound, status mix, duration distribution, and notable shifts. Use when the user wants a quick pulse on production call activity, or invokes /bluejay:production-pulse. For failures use /bluejay:failed-call-triage; for slowness /bluejay:latency-triage.
---

# Production pulse

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: a fast, accurate read on production call activity over a window.

## Steps

1. **Set the window.** Default last 24h unless the user gives a range. Scope to the agent(s) the user cares about.
2. **Pull the numbers.** `list_call_logs` — use the `total` field for counts rather than enumerating. Break down by:
   - total volume,
   - inbound vs. outbound (`call_direction`),
   - status mix (completed / failed / no-answer),
   - duration distribution (note very short and very long calls).
3. **Call out shifts.** Anything notable vs. what's normal (spike in failures, unusual short-call rate). Link drill-downs to `https://app.getbluejay.ai/monitor/logs`.

## Notes
- This is production data via `list_call_logs` — don't mix in simulation results.
- If a broad query returns zero but calls should exist, retry once with optional filters (`duration_min`/`max`, `status`) removed before reporting "no traffic".
- For failures specifically, hand off to `/bluejay:failed-call-triage`; for slowness, `/bluejay:latency-triage`.
