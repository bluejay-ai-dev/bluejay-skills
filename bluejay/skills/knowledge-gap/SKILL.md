---
name: knowledge-gap
description: Turn "the agent fumbled some questions" into a concrete, prioritized list of knowledge-base additions, grounded in real failed simulation results and transcripts. Use when the user wants to find what the agent doesn't know and should, or invokes /bluejay:knowledge-gap.
---

# Find knowledge gaps

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: turn "the agent fumbled some questions" into a concrete list of knowledge-base additions.

## Steps

1. **Pick the source.** A specific simulation/run is best (`get_simulations_by_agent` → `get_simulation_runs` → `get_simulation_results`). Look for results that failed on accuracy/answer-quality metrics or where the transcript shows "I don't know" / wrong answers. Read the failing transcripts (`get_simulation_result`, or `get_trace` for the underlying turns).
2. **Cluster the gaps.** Group the fumbled questions into themes (e.g. "return policy edge cases", "financing terms", "hours for holiday weekends").
3. **Report.** Table of theme | example question the agent missed | suggested KB addition. Prioritize by how often the theme came up.

## Notes
- Ground every gap in a real fumbled question from the results — don't speculate about gaps you didn't observe.
- The Bluejay MCP does not expose knowledge-base contents, so you can't read the agent's KB directly. Frame each item as a suggested addition and, where it matters, ask the user whether the theme is already covered but stale vs. missing entirely.
