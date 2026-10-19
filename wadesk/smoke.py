"""--smoke: start the real window and Qt WebEngine on a local page, check it, and exit.

Used by CI to prove that a build (or a source checkout) starts on this machine. Nothing is
loaded from the network. Exit codes: 0 passed, 1 a check failed, 2 timed out, 3 renderer crashed.
"""

import json
import sys
import traceback

from PySide6.QtCore import QTimer, QUrl

TIMEOUT_MS = 120_000
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>(3) WhatsApp</title></head>
<body><div id="app"><div id="pane-side"><div role="listitem">Smoke test</div></div></div></body></html>
"""
PROBE = ("JSON.stringify({ua: navigator.userAgent, title: document.title,"
         " privacy: !!document.getElementById('wadesk-privacy')})")


def _say(text: str) -> None:
    print(f"smoke: {text}", file=sys.stderr, flush=True)


class SmokeTest:
    def __init__(self, app, controller):
        self.app = app
        self.c = controller
        self.code = None
        page = controller.page
        page.loadFinished.connect(self._loaded)
        page.renderProcessTerminated.connect(lambda *_: self._finish(3, "the render process crashed"))
        QTimer.singleShot(TIMEOUT_MS, lambda: self._finish(2, "timed out"))
        page.grant_defaults()
        page.setHtml(PAGE, QUrl("https://web.whatsapp.com/"))

    def _loaded(self, ok: bool) -> None:
        if not ok:
            self._finish(1, "the local page did not load")
            return
        # Give the title (unread badge) and the injected privacy style a moment to arrive.
        QTimer.singleShot(1500, lambda: self.c.page.runJavaScript(PROBE, 0, self._check))

    def _check(self, raw) -> None:
        try:
            info = json.loads(raw or "{}")
            problems = []
            if "QtWebEngine" in info.get("ua", "") or "Chrome/" not in info.get("ua", ""):
                problems.append(f"unexpected user agent: {info.get('ua')!r}")
            if not info.get("privacy"):
                problems.append("privacy style was not injected")
            if not self.c.window.windowTitle().startswith("(3)"):
                problems.append(f"unread count not read from the title: {self.c.window.windowTitle()!r}")
            if not self.c.server.isListening():
                problems.append("single-instance server is not listening")
            if problems:
                self._finish(1, "; ".join(problems))
            else:
                _say(f"user agent {info['ua']}")
                self._finish(0, "passed")
        except Exception:  # noqa: BLE001 - report anything instead of hanging until the timeout
            self._finish(1, traceback.format_exc())

    def _finish(self, code: int, message: str) -> None:
        if self.code is not None:
            return
        self.code = code
        _say(message)
        self.c.window.quit_for_real()
        self.app.exit(code)


def run(app, make_controller) -> int:
    try:
        controller = make_controller()
        test = SmokeTest(app, controller)  # noqa: F841 (keeps the connections alive)
        code = app.exec()
    except Exception:  # noqa: BLE001 - a frozen GUI build must exit, not show an error dialog
        _say(traceback.format_exc())
        return 1
    return code if test.code is None else test.code
