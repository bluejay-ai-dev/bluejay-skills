---
name: coverage-audit
description: Map which branches of a Bluejay agent's conversation flow are exercised by existing test personas and which are blind spots, then propose personas to close the gaps. Use when the user wants to find untested paths, audit test coverage, or invokes /bluejay:coverage-audit.
---

# Audit test coverage

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: show which branches of an agent's conversation flow are exercised by existing tests and which are blind spots, then propose personas to close the gaps.

## Steps

1. **Pick the agent.** Use the agent from the conversation or `list_agents`.
2. **Read the flow.** Call `get_workflow_summary(agent_id)` to get the nodes and edges (each edge's `condition` is the transition trigger — e.g. "caller asks about returns"). This is the set of paths the agent can take.
3. **Read the existing tests.** For the agent's simulation(s) (`get_simulations_by_agent`), pull current personas with `get_digital_humans_by_simulation` and read their intents / success criteria.
4. **Map coverage.** Match each meaningful branch (edge condition / node) to whether any persona's intent plausibly drives the agent down it. Be conservative — only count a branch as covered if a persona clearly targets it.
5. **Report.** A coverage table: branch / condition | covered? | which persona(s). Then a **gaps** list of branches no persona reaches.
6. **Propose fixes.** For each gap, propose a concrete persona (intent + success_criteria) that would exercise it. Offer to generate them via the `/bluejay:persona-suite` skill.

## Notes
- This audits *coverage*, not quality — a covered branch can still fail; pair with `/bluejay:agent-regression` for scores.
- If the agent has no workflow graph (single-prompt agent), fall back to auditing coverage against the agent's stated intents/prompt rather than nodes/edges, and say so.
