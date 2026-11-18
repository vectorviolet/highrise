"""The browser side of the web build (pygbag, `sys.platform == "emscripten"`).

Everything that touches the browser lives here, so the game asks `is_web()` and
calls these functions, and tests replace them (or pygbag's `platform.window`)
with fakes. On desktop none of them is ever called.
"""

import sys
from typing import Any

_notice: Any = None


def is_web() -> bool:
    """True in the browser build. Read at call time (not import time) so a test
    can pretend to be the browser by patching `sys.platform`."""
    return sys.platform == "emscripten"


def _window() -> Any:
    """pygbag's `platform.window`: the browser's JavaScript `window`."""
    import platform

    # pygbag's platform module adds `window`; the standard library's has none.
    return platform.window  # type: ignore[attr-defined]


def open_in_new_tab(url: str) -> None:
    """Opens `url` in a new browser tab. Needs a click or key press (a button
    press is one), or the browser's pop-up blocker refuses."""
    _window().open(url, "_blank")


def is_fullscreen() -> bool:
    """True while the page is in the browser's fullscreen mode."""
    return _window().document.fullscreenElement is not None


def toggle_fullscreen() -> None:
    """Enters the browser's fullscreen mode, or leaves it. The browser only
    allows this from a click or key press (a button press is one)."""
    window = _window()
    if window.document.fullscreenElement is not None:
        window.document.exitFullscreen()
    else:
        window.document.documentElement.requestFullscreen()


def show_notice(message: str) -> None:
    """Persistent, nonblocking browser notice; cleared after a successful retry."""
    global _notice
    document = _window().document
    if _notice is None:
        notice = document.createElement("div")
        notice.id = "highrise-storage-notice"
        notice.setAttribute("role", "status")
        notice.style.cssText = (
            "position:fixed;top:8px;left:10%;right:10%;z-index:9999;"
            "padding:12px;background:#fff3cd;color:#522000;white-space:pre-line;"
            "font:18px sans-serif;text-align:center;pointer-events:none"
        )
        document.body.appendChild(notice)
        _notice = notice
    _notice.textContent = message
    _notice.style.display = "block" if message else "none"
