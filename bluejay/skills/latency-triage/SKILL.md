---
name: latency-triage
description: Locate where a Bluejay agent's response time is being spent and which calls are worst, then name the most likely contributor (LLM, TTS first-audio, tool round-trips) and a concrete next step. Use when the agent feels slow and the user wants to find where the time goes, or invokes /bluejay:latency-triage.
---

# Triage latency

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: locate where response time is being spent and which calls are worst, then suggest where to dig.

## Steps

1. **Scope.** Agent + time range from the conversation, or ask the user.
2. **Worst offenders.** `list_call_logs` and sort/inspect the longest or slowest calls; pull the worst few back by their `call_ids` (`get_call_log`) and use `get_trace` / `get_span` to read where the lag lands in the conversation.
3. **Attribute + recommend.** Latency in voice agents usually comes from a handful of places — model/LLM response time, TTS first-audio, and tool/integration round-trips. Based on where the delay sits in the traces/transcripts, name the most likely contributor and a concrete next step (model choice, streaming/first-audio settings, slow tool).

## Notes
- Distinguish per-call latency from latency-under-load — if it's only slow at scale, route to `/bluejay:load-test`.
- Be explicit about what you can vs. can't see: if component-level timing isn't exposed via the spans, say the attribution is inferred from transcript timing, not measured.
