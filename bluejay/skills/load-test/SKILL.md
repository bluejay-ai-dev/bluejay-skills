---
name: load-test
description: See how a voice agent holds up under many concurrent calls — dropped calls, latency spikes, error rates — by running a high-concurrency Bluejay simulation. Use when the user wants to load-test, stress-test capacity, or check behavior under concurrent calls, or invokes /bluejay:load-test.
---

# Load-test an agent

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: find where an agent degrades under concurrency — dropped calls, latency spikes, error rates — not whether individual answers are correct.

## Steps

1. **Resolve the agent.** Confirm the target and the concurrency level to test (ask if not given — e.g. 25, 50, 100 simultaneous calls).
2. **Create a load simulation.** `create_simulation` linked to the agent with a high concurrent-calls setting matching the target. Keep it separate from quality sims so results aren't conflated.
3. **Populate volume.** `list_phone_numbers` for caller IDs, then `generate_digital_humans` (`simulation_id` set) for a batch of straightforward callers — variety matters less than volume here. Confirm the count before generating a large set.
4. **Run it.** `queue_simulation_run`; report the run link.
5. **Report degradation.** When COMPLETED, `get_simulation_results` and focus on: completion vs. dropped/errored calls, latency distribution under load vs. a baseline single-call run, and any failure that only appears at scale. Present the latency breakdown as a table.

## Notes
- This tests **capacity**, not answer quality — pair with `/bluejay:agent-regression` for correctness.
- Be deliberate about concurrency: a real load test consumes phone-pool capacity and minutes. Confirm the scale with the user before queuing large runs.
