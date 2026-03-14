#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Resolve MCP server command ────────────────────────────────────

resolve_mcp_command() {
    if command -v paper-agent-mcp &>/dev/null; then
        MCP_CMD="$(which paper-agent-mcp)"
        MCP_ARGS='[]'
        info "Found paper-agent-mcp in PATH: $MCP_CMD"
        return 0
    fi

    local venv_bin="$REPO_ROOT/.venv/bin/paper-agent-mcp"
    if [ -x "$venv_bin" ]; then
        MCP_CMD="$venv_bin"
        MCP_ARGS='[]'
        info "Found paper-agent-mcp in venv: $venv_bin"
        return 0
    fi

    local venv_python="$REPO_ROOT/.venv/bin/python"
    if [ -x "$venv_python" ]; then
        MCP_CMD="$venv_python"
        MCP_ARGS='["-m", "paper_agent.mcp.server"]'
        info "Using python -m fallback: $venv_python"
        return 0
    fi

    err "Cannot find paper-agent-mcp."
    err "  cd $REPO_ROOT && poetry install"
    exit 1
}

resolve_mcp_command

# ── Install Claude Code plugin ────────────────────────────────────

install_claude_code() {
    local claude_dir="$HOME/.claude"
    local plugin_target="$claude_dir/plugins/local/paper-agent"
    local source_dir="$SCRIPT_DIR/claude-code"

    if [ ! -d "$claude_dir" ]; then
        warn "~/.claude not found, skipping Claude Code."
        return 1
    fi

    info "Installing Claude Code plugin..."
    mkdir -p "$plugin_target"

    cp -R "$source_dir/.claude-plugin" "$plugin_target/"
    cp -R "$source_dir/commands"       "$plugin_target/"
    cp -R "$source_dir/skills"         "$plugin_target/"

    # Write .mcp.json with resolved path
    cat > "$plugin_target/.mcp.json" <<EOFJ
{
  "paper-agent": {
    "command": "$MCP_CMD",
    "args": $MCP_ARGS
  }
}
EOFJ

    ok "Claude Code plugin → $plugin_target"
    echo "  Commands: /start-my-day, /paper-search, /paper-analyze, /paper-collect"
    echo "           /paper-setup, /paper-compare, /paper-survey, /paper-download"
    echo ""
    return 0
}

# ── Install Cursor (global, for all projects) ─────────────────────

install_cursor_global() {
    local cursor_dir="$HOME/.cursor"

    if [ ! -d "$cursor_dir" ]; then
        warn "~/.cursor not found, skipping Cursor."
        return 1
    fi

    info "Installing Cursor skill + rule (global)..."

    # Skill
    local skill_target="$cursor_dir/skills/paper-agent"
    mkdir -p "$skill_target/references"
    cp "$REPO_ROOT/.cursor/skills/paper-agent/SKILL.md" "$skill_target/SKILL.md"
    cp "$REPO_ROOT/.cursor/skills/paper-agent/references/analysis-template.md" \
       "$skill_target/references/analysis-template.md"
    ok "Skill → $skill_target"

    # Rule
    mkdir -p "$cursor_dir/rules"
    cp "$REPO_ROOT/.cursor/rules/paper-agent.mdc" "$cursor_dir/rules/paper-agent.mdc"
    ok "Rule  → $cursor_dir/rules/paper-agent.mdc"

    # MCP config
    local mcp_config="$cursor_dir/mcp.json"
    if [ -f "$mcp_config" ]; then
        if grep -q '"paper-agent"' "$mcp_config" 2>/dev/null; then
            ok "MCP already configured in $mcp_config"
        else
            warn "$mcp_config exists, add paper-agent manually:"
            echo "  \"paper-agent\": { \"command\": \"$MCP_CMD\", \"args\": $MCP_ARGS }"
        fi
    else
        cat > "$mcp_config" <<EOFJ
{
  "mcpServers": {
    "paper-agent": {
      "command": "$MCP_CMD",
      "args": $MCP_ARGS
    }
  }
}
EOFJ
        ok "MCP   → $mcp_config"
    fi

    echo ""
    return 0
}

# ── Main ───────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Paper Agent — Global Plugin Installer          ║"
echo "║                                                  ║"
echo "║   Installs paper-agent to GLOBAL locations:      ║"
echo "║     • Claude Code → ~/.claude/plugins/local/     ║"
echo "║     • Cursor      → ~/.cursor/skills + rules     ║"
echo "║                                                  ║"
echo "║   Tip: use 'paper-agent setup claude-code' or    ║"
echo "║   'paper-agent setup cursor' for project-level.  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

claude_ok=false
cursor_ok=false

install_claude_code && claude_ok=true
install_cursor_global && cursor_ok=true

echo "────────────────────────────────────────"
if $claude_ok || $cursor_ok; then
    ok "Done! Restart IDE to activate."
    $claude_ok && echo "  ✓ Claude Code plugin (global)"
    $cursor_ok && echo "  ✓ Cursor skill + rule + MCP (global)"
else
    err "No supported IDE found."
    exit 1
fi
