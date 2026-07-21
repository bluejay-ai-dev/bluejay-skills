---
name: schedule-sim
description: Put a Bluejay simulation on autopilot at a recurring cadence, or audit and edit what's already scheduled. Use when the user wants to run a test automatically on a schedule (nightly, weekly), review existing schedules, or invokes /bluejay:schedule-sim.
---

# Schedule a recurring simulation

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: put a simulation on autopilot at a cadence the user wants, or audit what's already scheduled.

## Steps

1. **Clarify intent.** Creating a new schedule, or reviewing existing ones? To review, call `list_schedules` (no args) and present them as a table; `get_schedule` for detail.
2. **For a new schedule**, resolve the simulation (`get_simulations_by_agent`) and the cadence (e.g. nightly at a time, weekly). Confirm the simulation already has digital humans linked — a scheduled run with no personas is wasted.
3. **Create it.** `create_schedule` with the simulation and cadence. Confirm back the next run time in plain language.
4. **Edits / removal.** Use `update_schedule` to change cadence and `delete_schedule` to remove. Deleting is destructive — confirm the exact schedule before deleting.

## Notes
- A schedule re-runs the simulation **as configured** — if the persona set or metrics change, the schedule picks them up automatically. Mention this so the user knows edits to the sim affect future scheduled runs.
- Don't stack a near-duplicate schedule on a simulation that already has one; check `list_schedules` first.
