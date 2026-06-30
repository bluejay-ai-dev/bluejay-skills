#!/bin/sh
# Bluejay programmatic onboarding.
# Wires the Bluejay MCP server, skills, and the Python SDK into whatever
# AI coding tools you have installed (Claude Code, Codex, Gemini CLI, Cursor,
# Windsurf, Antigravity, Claude Desktop).
#
#   curl -fsSL https://raw.githubusercontent.com/bluejay-ai-dev/bluejay-skills/main/install.sh | sh
#   curl -fsSL ... | BLUEJAY_API_KEY=bj_xxx sh        # non-interactive
#
# Safe to re-run. POSIX sh, no bashisms.
# No `set -e`: tool probes are best-effort and may exit non-zero by design;
# the only fatal paths (missing/invalid key) call `exit 1` explicitly.
set -u

MCP_URL="https://api.getbluejay.ai/mcp"
API_BASE="https://api.getbluejay.ai/v1"
SKILLS_REPO="https://github.com/bluejay-ai-dev/bluejay-skills.git"
BAC_SKILL_RAW="https://raw.githubusercontent.com/bluejay-ai-dev/docs/main/key-concepts/bluejay-as-code/skill.txt"
SKILLS_DIR="$HOME/.bluejay/skills"
SDK_PKG="bluejay-sdk"

# ---------- pretty output ----------
if [ -t 1 ]; then B=$(printf '\033[1m'); D=$(printf '\033[2m'); G=$(printf '\033[32m'); Y=$(printf '\033[33m'); R=$(printf '\033[31m'); BL=$(printf '\033[38;5;33m'); LB=$(printf '\033[38;5;75m'); CY=$(printf '\033[38;5;51m'); X=$(printf '\033[0m'); else B=; D=; G=; Y=; R=; BL=; LB=; CY=; X=; fi
ok()   { printf '%s\n' "  ${G}✓${X} $*"; }
warn() { printf '%s\n' "  ${Y}!${X} $*"; }
err()  { printf '%s\n' "  ${R}✗${X} $*" >&2; }
sec() { printf '\n%s\n' "${B}$*${X}"; }

CONFIGURED=""   # space-separated list of tools we wired
mark() { CONFIGURED="$CONFIGURED $1"; }

have() { command -v "$1" >/dev/null 2>&1; }

banner() {
  printf '\n'
  printf '%s\n' "${BL}  ██████╗ ██╗     ██╗   ██╗███████╗     ██╗ █████╗ ██╗   ██╗${X}"
  printf '%s\n' "${BL}  ██╔══██╗██║     ██║   ██║██╔════╝     ██║██╔══██╗╚██╗ ██╔╝${X}"
  printf '%s\n' "${LB}  ██████╔╝██║     ██║   ██║█████╗       ██║███████║ ╚████╔╝ ${X}"
  printf '%s\n' "${LB}  ██╔══██╗██║     ██║   ██║██╔══╝  ██   ██║██╔══██║  ╚██╔╝  ${X}"
  printf '%s\n' "${CY}  ██████╔╝███████╗╚██████╔╝███████╗╚█████╔╝██║  ██║   ██║   ${X}"
  printf '%s\n' "${CY}  ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝ ╚════╝ ╚═╝  ╚═╝   ╚═╝   ${X}"
  printf '%s\n' "${D}                                    MCP · skills · SDK${X}"
}

# ---------- python (needed for SDK + safe JSON edits) ----------
PY=""
for c in python3 python; do have "$c" && { PY="$c"; break; }; done

# ---------- 1. API key ----------
resolve_key() {
  if [ "${BLUEJAY_API_KEY:-}" != "" ]; then
    ok "Using BLUEJAY_API_KEY from environment"
    return
  fi
  if [ ! -t 0 ] && [ ! -e /dev/tty ]; then
    err "No BLUEJAY_API_KEY set and no terminal to prompt."
    err "Re-run with:  curl -fsSL <url> | BLUEJAY_API_KEY=your_key sh"
    exit 1
  fi
  printf '%s\n' "  Get a key at ${B}https://app.getbluejay.ai/settings/api-keys${X}"
  printf '%s' "  Paste your Bluejay API key: "
  if [ -e /dev/tty ]; then
    stty -echo 2>/dev/null || true
    IFS= read -r BLUEJAY_API_KEY < /dev/tty || true
    stty echo 2>/dev/null || true
    printf '\n'
  else
    IFS= read -r BLUEJAY_API_KEY
  fi
  [ "${BLUEJAY_API_KEY:-}" != "" ] || { err "No key entered."; exit 1; }
  export BLUEJAY_API_KEY
}

verify_key() {
  have curl || { warn "curl not found — skipping key verification"; return; }
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "X-API-Key: $BLUEJAY_API_KEY" "$API_BASE/all-agents" 2>/dev/null || echo 000)
  case "$code" in
    200|201|204) ok "API key verified" ;;
    401)         err "Key rejected (401 Unauthorized). Check the key and retry."; exit 1 ;;
    403)         err "Key valid but has no organization (403). Finish setup in the dashboard."; exit 1 ;;
    000)         warn "Could not reach $API_BASE to verify (offline?) — continuing" ;;
    *)           warn "Unexpected status $code verifying key — continuing" ;;
  esac
}

persist_key() {
  line="export BLUEJAY_API_KEY=\"$BLUEJAY_API_KEY\""
  shell_name=$(basename "${SHELL:-sh}")
  case "$shell_name" in
    zsh)  rc="$HOME/.zshrc" ;;
    bash) rc="$HOME/.bashrc" ;;
    *)    rc="$HOME/.profile" ;;
  esac
  if [ -f "$rc" ] && grep -q "BLUEJAY_API_KEY" "$rc" 2>/dev/null; then
    ok "BLUEJAY_API_KEY already in $rc"
  else
    printf '\n# Bluejay\n%s\n' "$line" >> "$rc"
    ok "Added BLUEJAY_API_KEY to $rc"
  fi
}

# ---------- 2. SDK ----------
install_sdk() {
  if have uv; then
    if uv pip install --system --upgrade "$SDK_PKG" >/dev/null 2>&1 || uv pip install --upgrade "$SDK_PKG" >/dev/null 2>&1; then
      ok "Installed $SDK_PKG (uv)"; return
    fi
  fi
  if [ "$PY" != "" ]; then
    if "$PY" -m pip install --upgrade "$SDK_PKG" >/dev/null 2>&1 \
       || "$PY" -m pip install --user --upgrade "$SDK_PKG" >/dev/null 2>&1 \
       || "$PY" -m pip install --break-system-packages --user --upgrade "$SDK_PKG" >/dev/null 2>&1; then
      ok "Installed $SDK_PKG (pip)"; return
    fi
    warn "pip install failed — install manually:  $PY -m pip install $SDK_PKG"
    return
  fi
  warn "No Python found — skipping SDK. Install Python 3.10+, then: pip install $SDK_PKG"
}

# ---------- 3. portable skills (for non-Claude tools) ----------
download_skills() {
  mkdir -p "$SKILLS_DIR"
  if have git; then
    if [ -d "$SKILLS_DIR/.git" ]; then
      git -C "$SKILLS_DIR" pull --quiet --ff-only 2>/dev/null && ok "Updated skills in $SKILLS_DIR" || warn "Could not update skills repo"
    else
      rm -rf "$SKILLS_DIR"
      if git clone --quiet --depth 1 "$SKILLS_REPO" "$SKILLS_DIR" 2>/dev/null; then
        ok "Cloned skills to $SKILLS_DIR"
      else
        warn "git clone failed — skills not downloaded"
      fi
    fi
  else
    warn "git not found — skipping skill download (Claude plugin still works)"
  fi
  # Bluejay-as-Code skill is a portable plain-text system prompt
  if have curl; then
    curl -fsSL "$BAC_SKILL_RAW" -o "$SKILLS_DIR/bluejay-as-code.skill.txt" 2>/dev/null \
      && ok "Saved bluejay-as-code.skill.txt" || true
  fi
}

# AGENTS.md is read by Codex and a growing number of agents; point it at the skills.
write_agents_md() {
  target="$PWD/AGENTS.md"
  marker="<!-- bluejay-skills -->"
  [ -f "$target" ] && grep -q "$marker" "$target" 2>/dev/null && { ok "AGENTS.md already references Bluejay"; return; }
  {
    printf '\n%s\n' "$marker"
    printf '## Bluejay\n'
    printf 'This project uses Bluejay (voice/chat agent testing & monitoring).\n'
    printf -- '- MCP server `bluejay` is configured — use its tools to manage agents, simulations, digital humans, and metrics.\n'
    printf -- '- Python SDK: `from bluejay import Bluejay` (auth via BLUEJAY_API_KEY).\n'
    printf -- '- Skill guidance lives in %s (self-improve loop, Bluejay-as-Code).\n' "$SKILLS_DIR"
    printf '%s\n' "<!-- /bluejay-skills -->"
  } >> "$target"
  ok "Pointed $target at Bluejay skills"
}

# ---------- safe JSON merge (deep, preserves existing servers) ----------
# usage: merge_json <config-path> <server-json>
merge_json() {
  [ "$PY" != "" ] || { warn "no python — cannot edit $1"; return 1; }
  CONFIG_PATH="$1" SERVER_JSON="$2" "$PY" - <<'PY'
import json, os, pathlib, sys
p = pathlib.Path(os.path.expanduser(os.environ["CONFIG_PATH"]))
server = json.loads(os.environ["SERVER_JSON"])
data = {}
if p.exists() and p.stat().st_size:
    try:
        data = json.loads(p.read_text())
    except Exception:
        bak = p.with_suffix(p.suffix + ".bluejay.bak")
        p.replace(bak)
        sys.stderr.write(f"backed up unparseable config to {bak}\n")
        data = {}
if not isinstance(data, dict):
    data = {}
data.setdefault("mcpServers", {})
data["mcpServers"]["bluejay"] = server
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2) + "\n")
PY
}

KEY_JSON_HEADERS=""   # set in main() once the key is resolved

# ---------- 4. per-tool wiring ----------
configure_claude_code() {
  have claude || return
  sec "Claude Code"
  claude mcp remove bluejay -s user >/dev/null 2>&1 || true
  if claude mcp add --transport http --scope user bluejay "$MCP_URL" --header "X-API-Key: $BLUEJAY_API_KEY" >/dev/null 2>&1; then
    ok "MCP server wired (user scope)"
  else
    warn "claude mcp add failed — check 'claude mcp list'"
  fi
  if claude plugin marketplace add bluejay-ai-dev/bluejay-skills >/dev/null 2>&1; then
    claude plugin install bluejay@bluejay-skills >/dev/null 2>&1 \
      && ok "Skills plugin installed (/bluejay:self-improve)" \
      || warn "Plugin install failed — run: claude plugin install bluejay@bluejay-skills"
  else
    warn "Could not add plugin marketplace — run: claude plugin marketplace add bluejay-ai-dev/bluejay-skills"
  fi
  mark "Claude Code"
}

configure_claude_desktop() {
  case "$(uname -s)" in
    Darwin) cfg="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
    Linux)  cfg="$HOME/.config/Claude/claude_desktop_config.json" ;;
    *)      return ;;
  esac
  [ -d "$(dirname "$cfg")" ] || return   # only if Claude Desktop is present
  sec "Claude Desktop"
  merge_json "$cfg" '{"type":"http","url":"'"$MCP_URL"'","headers":'"$KEY_JSON_HEADERS"'}' \
    && { ok "Wired $cfg"; warn "Restart Claude Desktop to load it"; mark "Claude Desktop"; }
}

configure_cursor() {
  [ -d "$HOME/.cursor" ] || have cursor || return
  sec "Cursor"
  merge_json "$HOME/.cursor/mcp.json" '{"url":"'"$MCP_URL"'","headers":'"$KEY_JSON_HEADERS"'}' \
    && { ok "Wired ~/.cursor/mcp.json"; mark "Cursor"; }
}

configure_windsurf() {
  [ -d "$HOME/.codeium/windsurf" ] || have windsurf || return
  sec "Windsurf"
  merge_json "$HOME/.codeium/windsurf/mcp_config.json" '{"serverUrl":"'"$MCP_URL"'","headers":'"$KEY_JSON_HEADERS"'}' \
    && { ok "Wired ~/.codeium/windsurf/mcp_config.json"; mark "Windsurf"; }
}

configure_gemini() {
  [ -d "$HOME/.gemini" ] || have gemini || return
  sec "Gemini CLI"
  merge_json "$HOME/.gemini/settings.json" '{"httpUrl":"'"$MCP_URL"'","headers":'"$KEY_JSON_HEADERS"'}' \
    && { ok "Wired ~/.gemini/settings.json"; mark "Gemini CLI"; }
}

# Codex CLI — TOML. Native streamable-HTTP with http_headers.
# Old builds (<0.45) need [features] experimental_use_rmcp_client = true.
codex_needs_rmcp() {
  v=$(codex --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  [ "$v" != "" ] || return 1
  major=${v%%.*}; rest=${v#*.}; minor=${rest%%.*}
  [ "$major" -eq 0 ] && [ "$minor" -lt 45 ] 2>/dev/null
}

configure_codex() {
  [ -d "$HOME/.codex" ] || have codex || return
  sec "Codex CLI"
  [ "$PY" != "" ] || { warn "no python — cannot edit ~/.codex/config.toml"; return; }
  NEED_RMCP=0; codex_needs_rmcp && { NEED_RMCP=1; warn "old Codex detected — enabling rmcp client"; }
  CONFIG_PATH="$HOME/.codex/config.toml" URL="$MCP_URL" KEY="$BLUEJAY_API_KEY" NEED_RMCP="$NEED_RMCP" "$PY" - <<'PY'
import os, pathlib
p = pathlib.Path(os.path.expanduser(os.environ["CONFIG_PATH"]))
url = os.environ["URL"]
key = os.environ["KEY"].replace("\\", "\\\\").replace('"', '\\"')
need = os.environ.get("NEED_RMCP") == "1"
text = p.read_text() if p.exists() else ""
out, skip = [], False
for ln in text.splitlines():
    s = ln.strip()
    if s.startswith("[") and s.endswith("]"):
        skip = s == "[mcp_servers.bluejay]" or s.startswith("[mcp_servers.bluejay.")
    if not skip:
        out.append(ln)
while out and out[-1].strip() == "":
    out.pop()
if need and "experimental_use_rmcp_client" not in "\n".join(out):
    if "[features]" in out:
        i = out.index("[features]")
        out.insert(i + 1, "experimental_use_rmcp_client = true")
    else:
        out = ["[features]", "experimental_use_rmcp_client = true", ""] + out
out += ["", "[mcp_servers.bluejay]", f'url = "{url}"',
        f'http_headers = {{ "X-API-Key" = "{key}" }}']
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("\n".join(out).lstrip("\n") + "\n")
PY
  ok "Wired ~/.codex/config.toml"
  mark "Codex"
}

# Antigravity (Google) — serverUrl + headers, literal key (no env interpolation).
configure_antigravity() {
  [ -d "$HOME/.gemini/antigravity" ] || have antigravity || return
  sec "Antigravity"
  merge_json "$HOME/.gemini/antigravity/mcp_config.json" '{"serverUrl":"'"$MCP_URL"'","headers":'"$KEY_JSON_HEADERS"'}' \
    && { ok "Wired ~/.gemini/antigravity/mcp_config.json"; mark "Antigravity"; }
}

# ---------- run ----------
main() {
  banner

  sec "1 · Authenticate"
  resolve_key
  verify_key
  persist_key
  # build the header JSON now that the key is known (handles the interactive path)
  KEY_JSON_HEADERS='{"X-API-Key": "'"$BLUEJAY_API_KEY"'"}'

  sec "2 · Python SDK"
  install_sdk

  sec "3 · Skills"
  download_skills

  # 4 · tools (each is a no-op if the tool isn't installed)
  configure_claude_code
  configure_claude_desktop
  configure_cursor
  configure_windsurf
  configure_gemini
  configure_codex
  configure_antigravity

  # portable instructions for non-Claude agents — only inside a real project
  if [ -d "$PWD/.git" ] && [ "$PWD" != "$HOME" ]; then
    case "$CONFIGURED" in *Cursor*|*Windsurf*|*Codex*|*Gemini*|*Antigravity*) write_agents_md ;; esac
  fi

  sec "Done"
  if [ "$CONFIGURED" = "" ]; then
    warn "No supported coding tools detected. SDK + skills are installed."
    warn "Install Claude Code, Codex, Cursor, Windsurf, or Gemini CLI and re-run."
  else
    ok "Configured:$CONFIGURED"
  fi
  printf '%s\n' "  ${D}Open a new shell (or source your rc) so BLUEJAY_API_KEY is live.${X}"
  printf '%s\n' "  ${D}Claude Code: run /bluejay:self-improve · Docs: https://docs.getbluejay.ai${X}"
}

main
