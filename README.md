# localScreenControl

An MCP server that lets an AI assistant see and control your local desktop.

| Tool | What it does |
|------|--------------|
| `screenshot(monitor=1, max_width=1600)` | Screenshot of a monitor (1 = primary, 0 = all), downscaled to `max_width` |
| `click(x, y, button="left", clicks=1)` | Click at a pixel of the last screenshot (`clicks=2` = double-click) |
| `scroll(x, y, amount=-5)` | Mouse wheel at a point (negative = down) |
| `press_keys(keys)` | Key combos like `ctrl+tab`, `alt+f4`, `ctrl+shift+t`, `enter` |
| `type_text(text, paste=True)` | Enter text in the focused field, via clipboard paste (default) or real keystrokes |
| `get_clipboard()` / `set_clipboard(text)` | Read / write clipboard text (`ctrl+a`, `ctrl+c`, `get_clipboard` reads a whole page) |
| `wait_until_stable(timeout_ms=5000)` | Wait until the screen stops changing (page loads, dialogs, animations) |
| `batch(steps, screenshot_after=True)` | Run many actions in one call, then return a screenshot |

`batch` example:

```json
[{"action": "click", "x": 700, "y": 140},
 {"action": "type", "text": "Hello"},
 {"action": "keys", "keys": "enter"},
 {"action": "settle"},
 {"action": "wait", "ms": 300}]
```

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

- Coordinates are pixels of the most recent screenshot image. The server maps them back to the
  real screen (downscaling, DPI, monitor offset), so they always match what the AI saw.
- Linux clipboard needs `xclip` or `xsel` (`sudo apt install xclip`).
- Self-check: `.venv/bin/python test_server.py` (or `.venv\Scripts\python test_server.py`).
- Linux on Wayland: only X11/XWayland windows can be captured/controlled. Use an X11 session for full control.
- Key names follow [pynput's `Key`](https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key) (`ctrl`, `shift`, `alt`, `cmd`/`win`, `tab`, `enter`, `esc`, `f1`–`f20`, `up`, `page_down`, ...).

## Security

This server gives the connected AI full control over your mouse and keyboard.
Only connect it to clients you trust.

## License

MIT
