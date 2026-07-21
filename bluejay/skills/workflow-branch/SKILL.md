---
name: workflow-branch
description: Add a new branch (node + the edge that reaches it, like an escalation route) to a Bluejay agent's multi-node workflow graph, staging it on the Bluejay side and only pushing it live on explicit user approval. Use when the user wants to extend an agent's workflow with a new path or branch, or invokes /bluejay:workflow-branch.
---

# Add a workflow branch

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: insert a new branch into an agent's workflow graph correctly (node + the edge that reaches it), and only push it live if the user clearly approves.

## Steps

1. **Read the graph.** `get_workflow_summary(agent_id)` to see nodes + edges and pick where the new branch attaches. (Read-only, no confirmation.)
2. **Add the node.** `add_workflow_node(agent_id, name, prompt?, …)` — it returns a `node_id`. The node is unreachable until you connect it.
3. **Connect it.** `add_workflow_edge(agent_id, source_node_id, target_node_id, condition)` — set `condition` to the user-facing trigger (e.g. "caller mentions a complaint"). Strongly prefer setting a condition; without one the agent can't tell when to take the branch. Don't leave dangling nodes.
4. **These Bluejay-side edits need no confirmation** — they touch only the stored copy.
5. **Push live only on explicit approval.** `push_agent_workflow` (and `sync_agent_workflow` / `merge_elevenlabs_branches`) touch the live source of truth:
   - call it first with `confirmed=false`; it returns `{ needs_confirmation, preview, to_proceed }`,
   - relay the `preview` verbatim and ask the user to confirm,
   - only after a clear "yes", call again with `confirmed=true` and the same args.
   For ElevenLabs agents pushing to a non-default branch, use `list_elevenlabs_branches` and pass `branch_id`.

## Notes
- Do not push live unless the user explicitly asks to — default to staging the edit on the Bluejay side and reporting what you changed.
- This is the agent-level workflow (Workflow tab), distinct from `create_workflow`/`update_workflow` which edit Scenario Builder scenarios.
