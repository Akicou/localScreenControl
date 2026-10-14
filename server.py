"""MCP server: screenshot, click, hotkeys and typing on the local desktop."""
import ctypes
import io
import sys

if sys.platform == "win32":
    # Physical pixels everywhere, so screenshot coords == click coords on scaled displays.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

import mss
from mcp.server.mcpserver import Image, MCPServer
from PIL import Image as PILImage
from pynput.keyboard import Controller as Keyboard, Key, KeyCode
from pynput.mouse import Button, Controller as Mouse

mcp = MCPServer("localScreenControl")
keyboard, mouse = Keyboard(), Mouse()

ALIASES = {"control": "ctrl", "win": "cmd", "super": "cmd", "meta": "cmd", "windows": "cmd",
           "return": "enter", "escape": "esc", "del": "delete", "pgup": "page_up", "pgdn": "page_down",
           "pageup": "page_up", "pagedown": "page_down", "option": "alt"}


def parse_key(name: str):
    name = name.strip().lower()
    name = ALIASES.get(name, name)
    if len(name) == 1:
        return KeyCode.from_char(name)
    try:
        return Key[name]
    except KeyError:
        raise ValueError(f"Unknown key: {name!r}")


@mcp.tool()
def screenshot(monitor: int = 1) -> Image:
    """Screenshot a monitor (1 = primary, 0 = all monitors combined).
    Pixel coordinates in the image match the coordinates used by `click` (for monitor 1)."""
    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[monitor])
    buf = io.BytesIO()
    # ponytail: JPEG keeps 4K screens under MCP payload limits; switch to PNG if text gets too blurry.
    PILImage.frombytes("RGB", shot.size, shot.rgb).save(buf, "JPEG", quality=75)
    return Image(data=buf.getvalue(), format="jpeg")


@mcp.tool()
def click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """Click at screen pixel (x, y). button: left | right | middle. clicks: 2 for double-click."""
    mouse.position = (x, y)
    mouse.click(Button[button], clicks)
    return f"Clicked {button} x{clicks} at ({x}, {y})"


@mcp.tool()
def press_keys(keys: str) -> str:
    """Press a key or key combination, e.g. "ctrl+tab", "alt+f4", "ctrl+shift+t", "enter", "f5"."""
    *mods, last = [parse_key(k) for k in keys.split("+")]
    with keyboard.pressed(*mods):
        keyboard.tap(last)
    return f"Pressed {keys}"


@mcp.tool()
def type_text(text: str) -> str:
    """Type a string into the currently focused input (supports unicode)."""
    keyboard.type(text)
    return f"Typed {len(text)} characters"


if __name__ == "__main__":
    mcp.run()
