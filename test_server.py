"""Self-check: python test_server.py (takes a real screenshot, moves nothing)."""
import asyncio

import server


def test_coordinate_mapping():
    server.view.update(left=-1920, top=0, scale=1.6)
    assert server.to_screen(100, 50) == (-1920 + 160, 80)
    note, _ = server.capture(1, max_width=800)
    assert "800x" in note and server.view["scale"] >= 1


def test_batch_stops_on_error():
    report, = server.batch([{"action": "wait", "ms": 10}, {"action": "nope"}, {"action": "wait"}],
                           screenshot_after=False, delay_ms=0)
    assert report.splitlines()[0] == "1. waited 10 ms"
    assert "FAILED" in report.splitlines()[1] and len(report.splitlines()) == 2


def test_tools_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"screenshot", "click", "scroll", "press_keys", "type_text", "get_clipboard",
            "set_clipboard", "wait_until_stable", "batch"} <= names


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
