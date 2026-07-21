---
name: custom-metric-builder
description: Convert a user's quality bar into well-formed Bluejay custom metrics — sharp, single-purpose pass/fail (or enum/quantitative) checks with clear judge prompts that produce scorable judgements on each call. Use when the user wants to create evals or metrics that grade what an agent should or shouldn't do, or invokes /bluejay:custom-metric-builder.
---

# Build a custom metric / eval

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: convert the user's quality bar into well-formed custom metrics that produce clear, scorable judgements on each call.

## Steps

1. **Pin down what's being measured.** From the user's description, identify each distinct check. Prefer several sharp, single-purpose metrics over one vague catch-all. For each, decide the type that fits: boolean pass/fail (most checks), an enum/category, or a quantitative score.
2. **Resolve the agent.** `list_agents`; see existing metrics with `get_custom_metrics_by_agent` / `list_custom_metrics` so you don't duplicate one that already exists.
3. **Write the judge clearly.** For each metric give it a precise name and a judge prompt that states exactly what counts as pass vs. fail, with edge cases called out (a vague judge prompt is the #1 cause of noisy scores).
4. **Create them.** Use `create_custom_metric` for one, or `create_custom_metrics` for a batch. Confirm back the list with each metric's pass condition in one line.
5. **Offer to validate.** Suggest running the metrics on a recent run (the `/bluejay:run-report` skill) so the user can see how they score and tighten any that look noisy.

## Notes
- Metrics attach to simulations and score their results; they do not run themselves — they apply when a run is evaluated.
- To refine a metric whose judging looks off, create a tightened version and re-test rather than guessing — judge-prompt wording dominates result quality.
