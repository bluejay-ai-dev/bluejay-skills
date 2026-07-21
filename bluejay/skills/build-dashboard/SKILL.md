---
name: build-dashboard
description: Design the right dashboard for watching a Bluejay agent's health — inspect the agent's real traffic and metrics, then hand the user a concrete, ready-to-build widget list (metric + chart type + filter) and a link to create it. Use when the user wants a dashboard of the metrics that matter for an agent, or invokes /bluejay:build-dashboard.
---

# Build a dashboard

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: hand the user the handful of widgets they should actually watch, grounded in what data exists for this agent — not a generic template.

Dashboards are created in the Bluejay app, not over the MCP, so this skill **designs** the dashboard and points the user at where to build it.

## Steps

1. **Scope.** Which agent(s) and what the dashboard is for (general health vs. a specific concern). Use the agent from the conversation if present.
2. **Check what data actually exists** so you don't recommend widgets that render empty:
   - `list_call_logs` (small window) — is there production traffic, and what's the status/direction mix?
   - `get_simulations_by_agent` + recent `get_simulation_results` — is there simulation history?
   - `get_custom_metrics_by_agent` — which custom metrics exist and which are weakest.
3. **Recommend the core widgets** (4–6, keep it tight) as a table: widget | metric | chart type | filter/time-range | why it matters. Cover call volume over time, success/pass rate, latency, and the agent's weakest custom metric(s) — but only those the data in step 2 supports.
4. **Point the user to build it.** Link `https://app.getbluejay.ai/monitor/dashboards` and note they can create a dashboard there and add each recommended widget. Offer to refine the list once they've seen the first cut.

## Notes
- Pick metrics that exist for this agent — a recommendation that renders empty is worse than omitting it.
- If neither production traffic nor simulation history exists yet, say so and suggest running a sim first (`/bluejay:run-simulation`) before there's anything worth charting.
