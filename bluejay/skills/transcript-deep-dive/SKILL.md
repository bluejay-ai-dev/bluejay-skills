---
name: transcript-deep-dive
description: Analyze one Bluejay call in depth — simulation result or production call — to explain not just that it failed but exactly where and why, and recommend one concrete fix. Use when the user wants to understand one specific call or test result in detail, or invokes /bluejay:transcript-deep-dive.
---

# Deep-dive a transcript

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: explain one call thoroughly — not just that it failed, but exactly where and why.

## Steps

1. **Locate the call.** For a simulation result use `get_simulation_result` (single) or `get_simulation_results` then the specific case. For a production call use `get_call_log` for the single call (or `list_call_logs` to find it first). For the underlying turn-by-turn detail use `get_trace` / `get_span`.
2. **Read the whole transcript**, not just the summary.
3. **Walk the conversation:**
   - the caller's actual goal,
   - the turn(s) where it went off the rails (quote them briefly),
   - which metric/criterion failed and the precise reason,
   - whether it's an agent-logic issue, a prompt gap, a tool/integration failure, or a knowledge gap.
4. **Recommend one concrete fix** tied to the failing turn (prompt change, guardrail, KB addition, workflow branch).

## Notes
- Quote sparingly and specifically — point at the exact turn, don't paste the whole transcript back.
- Link to the in-app result/call page rather than constructing raw recording URLs.
