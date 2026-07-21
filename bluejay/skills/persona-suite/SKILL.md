---
name: persona-suite
description: Turn a short description of the callers you want to test into a diverse, runnable set of Bluejay digital humans — varied intent, sentiment, language, and edge cases — attached to a simulation. Use when the user wants to populate a simulation with realistic test callers or personas, or invokes /bluejay:persona-suite.
---

# Build a persona suite

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: translate a free-form description of the callers you want to test into a diverse, runnable set of digital humans.

## Steps

1. **Resolve the brief.** You need: the target agent/simulation, roughly how many personas, and the segments to cover. Take what the user gave you and the agent already in the conversation first; only ask the user for what's genuinely missing (don't ask for things you can infer).
2. **Find or create the simulation.** `get_simulations_by_agent`, then reuse or `create_simulation`. Hold onto its `simulation_id`.
3. **Get a caller-ID number** via `list_phone_numbers` (org pool — the number personas call FROM).
4. **Generate the suite.** Call `generate_digital_humans` with `simulation_id` set and a prompt that expands the brief into varied personas. Deliberately vary:
   - **intent** (why they're calling),
   - **sentiment / difficulty** (calm vs. frustrated, cooperative vs. evasive),
   - **language / accent** where relevant,
   - **edge conditions** (missing info, wrong account, mid-call change of mind).
   Give each a concrete `backstory`, `goals`, and `success_criteria`. Prefer one `generate_digital_humans` call for the whole set over many `create_digital_human` calls.
5. **Confirm back.** Show a table of what was created: name | intent | language | difficulty | success criteria. Do not silently create dozens — if the count is large or would duplicate an existing big set, ask the user first.
6. **Offer the next step:** queue a run now (`queue_simulation_run`) or hand off to the `/bluejay:agent-regression` / `/bluejay:red-team-sweep` skills.

## Notes
- `simulation_id` must be set at creation — digital humans not linked to a simulation will make `queue_simulation_run` fail.
- Keep personas realistic, not cartoonish; the goal is coverage of real call variety.
