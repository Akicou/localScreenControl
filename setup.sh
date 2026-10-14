#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
  echo "Warning: Wayland session detected. Input/screenshots only work for X11/XWayland apps; an X11 session is recommended." >&2
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

PY="$PWD/.venv/bin/python"
SRV="$PWD/server.py"

if command -v claude >/dev/null; then
  claude mcp add --scope user localScreenControl -- "$PY" "$SRV"
  echo "Registered with Claude Code."
fi

cat <<EOF

MCP client config (e.g. Claude Desktop):
{
  "mcpServers": {
    "localScreenControl": { "command": "$PY", "args": ["$SRV"] }
  }
}
EOF
