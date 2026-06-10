# Provider: livekit-local

**Use when:** a self-hosted LiveKit agent (Python worker) you can run on your machine. The **local run is the test target** — inherently non-production, so prod is never touched; changes reach prod only via the PR.

**Config fields this provider adds:**
- `livekit_agent_name` — the name the worker registers under (Bluejay dispatches to it).
- `worker_cmd` — command to run the worker locally (e.g. `uv run python src/agent.py dev`).

## Setup (onboarding — detect → confirm → ask)
1. **Run command + agent name.** Detect the entrypoint and `@server.rtc_session(agent_name="…")` (or `WorkerOptions(agent_name=…)`); read the run command from README/pyproject (default `uv run python src/agent.py dev`). Confirm. Ask only if not found.
2. **Prompt file.** Detect a dedicated prompt file (e.g. `src/prompts/*.md`) or the inline `instructions=` string. Confirm which one the loop should edit.
3. **Credentials.** Check `.env.local` has `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`. If missing: `lk cloud auth` then `lk app env -w -d .env.local`. **Must be the same LiveKit project Bluejay dispatches into**, or the worker never receives the job and runs time out.
4. **One-time deps.** `uv sync`; `uv run python <entrypoint> download-files` (Silero VAD + turn detector).

## Preflight (every run)
- `.env.local` populated; deps installed; `worker_cmd` starts and registers under `livekit_agent_name`.

## Apply (make a prompt change live)
- Edit `prompt_file`, then restart the worker: `pkill -f` a unique fragment of `worker_cmd`, relaunch it in the background, wait for re-registration. The worker reads `prompt_file` at session start, so a restart guarantees the new prompt is live.

## Run (trigger the test)
- Ensure the worker is running. `queue_simulation_run(simulation_id, livekit_agent_name)` → poll `get_simulation_runs` / `get_simulation` until done → `get_simulation_results(run_id)`.

## Teardown
- Always stop the worker on exit (and after an abort, before restoring the prompt).
