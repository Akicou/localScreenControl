# localScreenControl

An MCP server that lets an AI assistant see and control your local desktop.

| Tool | What it does |
|------|--------------|
| `screenshot(monitor=1)` | Screenshot of a monitor (1 = primary, 0 = all) |
| `click(x, y, button="left", clicks=1)` | Click at a screen pixel (`clicks=2` = double-click) |
| `press_keys(keys)` | Key combos like `ctrl+tab`, `alt+f4`, `ctrl+shift+t`, `enter` |
| `type_text(text)` | Type a string into the focused field (unicode supported) |

Works on Windows and Linux (X11). Requires Python 3.10+.

## Setup

**Windows (PowerShell)**

```powershell
git clone https://github.com/Akicou/localScreenControl
cd localScreenControl
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

**Linux**

```bash
git clone https://github.com/Akicou/localScreenControl
cd localScreenControl
./setup.sh
```

The script creates a `.venv`, installs dependencies, registers the server with
Claude Code (if `claude` is on your PATH) and prints a JSON config snippet for
other MCP clients such as Claude Desktop.

## Notes

- Coordinates are physical pixels of the primary monitor, matching the screenshot.
- Linux on Wayland: only X11/XWayland windows can be captured/controlled. Use an X11 session for full control.
- Key names follow [pynput's `Key`](https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key) (`ctrl`, `shift`, `alt`, `cmd`/`win`, `tab`, `enter`, `esc`, `f1`–`f20`, `up`, `page_down`, ...).

## Security

This server gives the connected AI full control over your mouse and keyboard.
Only connect it to clients you trust.

## License

MIT
