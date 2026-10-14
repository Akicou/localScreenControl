"""MCP server: screenshot, click, scroll, hotkeys, typing, clipboard and batched actions on the local desktop."""
import ctypes
import io
import sys
import time

if sys.platform == "win32":
    # Physical pixels everywhere, so screen grabs and mouse positions share one coordinate space.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

import mss
import pyperclip
from mcp.server.mcpserver import Image, MCPServer
from PIL import Image as PILImage, ImageChops
from pynput.keyboard import Controller as Keyboard, Key, KeyCode
from pynput.mouse import Button, Controller as Mouse

mcp = MCPServer("localScreenControl")
keyboard, mouse = Keyboard(), Mouse()

ALIASES = {"control": "ctrl", "win": "cmd", "super": "cmd", "meta": "cmd", "windows": "cmd",
           "return": "enter", "escape": "esc", "del": "delete", "pgup": "page_up", "pgdn": "page_down",
           "pageup": "page_up", "pagedown": "page_down", "option": "alt"}
PASTE = "cmd+v" if sys.platform == "darwin" else "ctrl+v"

# Maps image pixels of the last screenshot to physical screen pixels: screen = left + x * scale.
view = {"left": 0, "top": 0, "scale": 1.0, "monitor": 1}


def parse_key(name: str):
    name = name.strip().lower()
    name = ALIASES.get(name, name)
    if len(name) == 1:
        return KeyCode.from_char(name)
    try:
        return Key[name]
    except KeyError:
        raise ValueError(f"Unknown key: {name!r}")


def to_screen(x: int, y: int) -> tuple[int, int]:
    return round(view["left"] + x * view["scale"]), round(view["top"] + y * view["scale"])


def grab(monitor: int):
    with mss.mss() as sct:
        mon = sct.monitors[monitor]
        shot = sct.grab(mon)
    return mon, PILImage.frombytes("RGB", shot.size, shot.rgb)


def capture(monitor: int = 1, max_width: int = 1600) -> list:
    mon, img = grab(monitor)
    scale = max(1.0, img.width / max_width)
    if scale > 1:
        img = img.resize((round(img.width / scale), round(img.height / scale)), PILImage.LANCZOS)
    view.update(left=mon["left"], top=mon["top"], scale=scale, monitor=monitor)
    buf = io.BytesIO()
    # ponytail: JPEG keeps payloads small; switch to PNG if small text gets too blurry.
    img.save(buf, "JPEG", quality=80)
    note = f"Screenshot {img.width}x{img.height} (monitor {monitor}). Pass coordinates from this image to click/scroll."
    return [note, Image(data=buf.getvalue(), format="jpeg")]


@mcp.tool()
def screenshot(monitor: int = 1, max_width: int = 1600) -> list:
    """Screenshot a monitor (1 = primary, 0 = all monitors combined), downscaled to at most max_width px.
    click/scroll coordinates are pixels of the most recent screenshot image; scaling and monitor
    offset are handled by the server, so use the image coordinates as-is."""
    return capture(monitor, max_width)


@mcp.tool()
def click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """Click at (x, y) in the last screenshot's pixel space. button: left | right | middle. clicks: 2 = double-click."""
    mouse.position = to_screen(x, y)
    mouse.click(Button[button], clicks)
    return f"Clicked {button} x{clicks} at ({x}, {y})"


@mcp.tool()
def scroll(x: int, y: int, amount: int = -5) -> str:
    """Scroll the mouse wheel at (x, y) (last screenshot's pixel space). Negative = down, positive = up.
    One unit is one wheel notch (~3 lines)."""
    mouse.position = to_screen(x, y)
    mouse.scroll(0, amount)
    return f"Scrolled {amount} at ({x}, {y})"


@mcp.tool()
def press_keys(keys: str) -> str:
    """Press a key or key combination, e.g. "ctrl+tab", "alt+f4", "ctrl+shift+t", "enter", "f5"."""
    *mods, last = [parse_key(k) for k in keys.split("+")]
    with keyboard.pressed(*mods):
        keyboard.tap(last)
    return f"Pressed {keys}"


@mcp.tool()
def type_text(text: str, paste: bool = True) -> str:
    """Enter text into the focused input. paste=True (default) inserts it via the clipboard, which is
    instant and doesn't drop characters in web apps; the previous clipboard content is restored.
    Use paste=False to send real keystrokes (e.g. for fields that block pasting)."""
    if not paste:
        keyboard.type(text)
        return f"Typed {len(text)} characters"
    old = pyperclip.paste()
    pyperclip.copy(text)
    press_keys(PASTE)
    time.sleep(0.15)  # let the app read the clipboard before restoring it
    pyperclip.copy(old)
    return f"Pasted {len(text)} characters"


@mcp.tool()
def get_clipboard() -> str:
    """Return the clipboard text. Combine with ctrl+a / ctrl+c to read a whole page or document at once."""
    return pyperclip.paste()


@mcp.tool()
def set_clipboard(text: str) -> str:
    """Put text on the clipboard."""
    pyperclip.copy(text)
    return f"Clipboard set ({len(text)} characters)"


@mcp.tool()
def wait_until_stable(timeout_ms: int = 5000, monitor: int = 1) -> str:
    """Wait until the screen stops changing (loading, animations, dialogs opening), up to timeout_ms."""
    end, prev = time.monotonic() + timeout_ms / 1000, None
    while time.monotonic() < end:
        # ponytail: thumbnail diff with 0.5% tolerance so cursors/spinners don't count; add a region param if too coarse.
        img = grab(monitor)[1].resize((320, 180)).convert("L")
        if prev is not None:
            changed = sum(1 for d in ImageChops.difference(img, prev).getdata() if d > 24)
            if changed < 0.005 * 320 * 180:
                return "Screen is stable"
        prev = img
        time.sleep(0.25)
    return f"Screen still changing after {timeout_ms} ms"


ACTIONS = {"click": click, "scroll": scroll, "keys": press_keys, "type": type_text,
           "set_clipboard": set_clipboard, "settle": wait_until_stable}


@mcp.tool()
def batch(steps: list[dict], screenshot_after: bool = True, delay_ms: int = 150) -> list:
    """Run several actions in one call, then optionally return a screenshot.
    Each step is {"action": ..., **args}:
      click {x, y, button?, clicks?} | scroll {x, y, amount?} | keys {keys} | type {text, paste?}
      set_clipboard {text} | wait {ms} | settle {timeout_ms?} (wait until the screen stops changing)
    delay_ms is paused after every step. Stops at the first failing step and reports it."""
    log = []
    for i, step in enumerate(steps, 1):
        args = dict(step)
        action = args.pop("action", None)
        try:
            if action == "wait":
                time.sleep(args.get("ms", 500) / 1000)
                log.append(f"{i}. waited {args.get('ms', 500)} ms")
            elif action in ACTIONS:
                log.append(f"{i}. {ACTIONS[action](**args)}")
            else:
                raise ValueError(f"unknown action {action!r}")
        except Exception as e:
            log.append(f"{i}. FAILED {step}: {e}")
            break
        time.sleep(delay_ms / 1000)
    report = "\n".join(log)
    return [report, *capture(view["monitor"])[1:]] if screenshot_after else [report]


if __name__ == "__main__":
    mcp.run()
