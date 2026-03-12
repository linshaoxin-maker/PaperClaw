#!/usr/bin/env bash
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

info()  { echo -e "${BOLD}${GREEN}✓${RESET} $1"; }
warn()  { echo -e "${BOLD}${YELLOW}!${RESET} $1"; }
error() { echo -e "${BOLD}${RED}✗${RESET} $1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "\n${BOLD}Paper Agent Installer${RESET}\n"

# ── 1. Find best Python ──
PYTHON=""
BEST_MINOR=0

candidates=(python python3)
# conda / venv activated Python comes first in PATH via `python`,
# also check explicit conda path in case PATH ordering is off
if [ -n "${CONDA_PREFIX:-}" ] && [ -x "$CONDA_PREFIX/bin/python" ]; then
    candidates=("$CONDA_PREFIX/bin/python" "${candidates[@]}")
fi
if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    candidates=("$VIRTUAL_ENV/bin/python" "${candidates[@]}")
fi

for candidate in "${candidates[@]}"; do
    if command -v "$candidate" &>/dev/null; then
        PY_MAJOR=$("$candidate" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo 0)
        PY_MINOR=$("$candidate" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo 0)
        if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -gt "$BEST_MINOR" ]; then
            BEST_MINOR=$PY_MINOR
            PYTHON="$candidate"
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    error "Python 3 not found."
    echo ""
    echo "  Please install Python 3.10+ first:"
    echo ""
    echo "    macOS:   brew install python"
    echo "    Ubuntu:  sudo apt install python3"
    echo "    Windows: https://www.python.org/downloads/"
    echo "    Conda:   conda create -n paper python=3.11 && conda activate paper"
    echo ""
    exit 1
fi

PY_VERSION=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

if [ "$BEST_MINOR" -lt 10 ]; then
    error "Python 3.10+ required. Best found: $PY_VERSION ($PYTHON)"
    echo ""
    echo "  Suggestions:"
    echo ""
    echo "    Conda:   conda create -n paper python=3.11 && conda activate paper"
    echo "    macOS:   brew upgrade python"
    echo "    Ubuntu:  sudo apt install python3.11"
    echo ""
    echo "  Activate the right environment, then re-run: ./install.sh"
    exit 1
fi
info "Python $PY_VERSION ($PYTHON)"

# ── 2. Ensure pipx ──
PIPX_CMD=()

if command -v pipx &>/dev/null; then
    info "pipx found"
    PIPX_CMD=(pipx)
else
    warn "pipx not found, installing (via pip)..."

    if ! "$PYTHON" -m pip --version &>/dev/null; then
        error "pip is not available for: $PYTHON"
        echo ""
        echo "  Please install pip first, then re-run: ./install.sh"
        echo ""
        echo "    macOS (python.org): https://www.python.org/downloads/"
        echo "    Ubuntu/Debian:      sudo apt install python3-pip"
        echo "    Conda:              conda install pip"
        echo ""
        exit 1
    fi

    # If we're inside a writable env (conda/venv), install into it.
    # Otherwise, install to user site-packages to avoid needing sudo.
    if [ -n "${CONDA_PREFIX:-}" ] || [ -n "${VIRTUAL_ENV:-}" ]; then
        "$PYTHON" -m pip install --upgrade pipx
    else
        "$PYTHON" -m pip install --user --upgrade pipx
    fi

    # Prefer invoking pipx via the selected Python to avoid PATH issues.
    if "$PYTHON" -m pipx --version &>/dev/null; then
        PIPX_CMD=("$PYTHON" -m pipx)
        # Best-effort: make sure pipx's bin dir is discoverable in future shells.
        "$PYTHON" -m pipx ensurepath &>/dev/null || true
        info "pipx installed"
    else
        # Last-resort fallback: try Homebrew if present.
        if command -v brew &>/dev/null; then
            warn "pipx install via pip failed; trying Homebrew..."
            brew install pipx
            PIPX_CMD=(pipx)
            info "pipx installed"
        else
            error "pipx installation failed."
            echo ""
            echo "  Try installing manually:"
            echo "    $PYTHON -m pip install --user --upgrade pipx"
            echo ""
            exit 1
        fi
    fi

    # Common pipx bin locations (used for this script run).
    export PATH="$HOME/.local/bin:$HOME/.local/pipx/bin:$PATH"
fi

# ── 3. Install paper-agent ──
echo ""
if command -v paper-agent &>/dev/null; then
    warn "paper-agent already installed, upgrading..."
    "${PIPX_CMD[@]}" install --force "$SCRIPT_DIR"
else
    "${PIPX_CMD[@]}" install "$SCRIPT_DIR"
fi

# ── 4. Verify ──
echo ""

PAPER_AGENT_BIN=""
if command -v paper-agent &>/dev/null; then
    PAPER_AGENT_BIN="paper-agent"
elif "${PIPX_CMD[@]}" run paper-agent --help &>/dev/null; then
    PAPER_AGENT_BIN="${PIPX_CMD[*]} run paper-agent"
fi

if [ -n "$PAPER_AGENT_BIN" ]; then
    VERSION=$($PAPER_AGENT_BIN --help 2>/dev/null | head -1 || echo "installed")
    info "paper-agent installed successfully!"
    echo ""
    echo -e "  ${BOLD}Get started:${RESET}"
    echo "    paper-agent init       # configure research interests & LLM"
    echo "    paper-agent collect    # fetch papers from arXiv"
    echo "    paper-agent digest     # daily recommendations"
    echo "    paper-agent            # interactive mode"
    echo ""
else
    error "Installation finished but 'paper-agent' is not available in PATH."
    echo ""
    echo "  If you installed pipx via pip, you may need to add pipx's bin dir:"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$HOME/.local/pipx/bin:\$PATH\""
    echo ""
    echo "  Then restart your terminal or run: source ~/.zshrc"
    exit 1
fi
