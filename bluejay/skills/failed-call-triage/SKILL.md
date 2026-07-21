---
name: failed-call-triage
description: Turn a pile of failed Bluejay production calls into a ranked list of failure modes the user can act on — clustered from real transcripts, with counts, examples, and prioritized fixes. Use when the user wants to know why live calls are failing and what to fix first, or invokes /bluejay:failed-call-triage.
---

# Triage failed calls

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: turn a pile of failed production calls into a ranked list of failure modes the user can actually act on.

## Steps

1. **Pull the failures.** Call `list_call_logs` scoped to failures. Apply the user's time range (default last 24h) and the agent(s) in scope. Use `status` / `call_direction` filters only if the user asked for them.
2. **Guard against false zeros.** If the query returns nothing but context suggests calls exist, retry once with the optional filters removed (drop `duration_min`/`duration_max`/`status` first) before concluding there are no failures.
3. **Sample transcripts.** For a representative subset, fetch detail (`get_call_log` per call, or `list_call_logs` with `call_ids`) so you can read what actually happened — don't cluster from metadata alone.
4. **Cluster by failure mode.** Group into recurring buckets, e.g.:
   - no-answer / immediate hangup,
   - dead air / long silences,
   - wrong or fabricated information,
   - failed escalation / transfer,
   - tool / integration error,
   - language mismatch,
   - loop / couldn't resolve the request.
5. **Report.** A ranked table: failure mode | count | share of failures | one example call (link via `https://app.getbluejay.ai/monitor/logs?call_id={id}`) | likely root cause. Then 2–4 prioritized recommendations tied to the biggest buckets.

## Notes
- This skill reads **production** logs via `list_call_logs` — do not use simulation tools here, and do not invent S3/recording URLs. Link to `https://app.getbluejay.ai/monitor/logs` instead.
- Quantify with the response's `total` for "how many", and be honest about sample size when you only read a subset of transcripts.
