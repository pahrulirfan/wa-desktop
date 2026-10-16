#!/usr/bin/env python3
"""Regenerate the README screenshots (docs/images/*.png).

The real WA Desktop UI is rendered, but the chat content comes from tools/demo_chat.html,
which contains fictional names and messages only - no real conversations are ever captured.
The script runs against a throw-away HOME, so your own settings and session are untouched.

Requires a running desktop session (X11):  python tools/make_screenshots.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"

# Work in a disposable home directory. Must happen before importing wadesk.
TMP = Path(tempfile.mkdtemp(prefix="wadesk-shots-"))
os.environ.update(HOME=str(TMP), XDG_CONFIG_HOME=str(TMP / "config"),
                  XDG_DATA_HOME=str(TMP / "data"), XDG_CACHE_HOME=str(TMP / "cache"))
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPoint, QPointF, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QMouseEvent, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QApplication

from wadesk import lock, paths
from wadesk.dialogs import SettingsDialog
from wadesk.tray import make_icon, render_base

PIN = "1234"


def seed_settings() -> None:
    cfg = paths.CONFIG_DIR
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "settings.json").write_text(json.dumps({
        "theme": "light", "lock_enabled": True, "lock_hash": lock.hash_pin(PIN),
        "lock_on_start": False, "lock_auto_minutes": 5, "close_to_tray": True,
    }))


def framed(pix: QPixmap, dark: bool, title: str | None = "WA Desktop", margin: int = 36,
           radius: int = 11) -> QImage:
    """Put a screenshot on a transparent canvas with a drop shadow and a simple title bar."""
    bar = 36 if title else 0
    w, h = pix.width(), pix.height() + bar
    img = QImage(w + 2 * margin, h + 2 * margin, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    for i in range(14):  # cheap soft shadow
        grow = 14 - i
        p.setBrush(QColor(0, 0, 0, 5 + i))
        p.drawRoundedRect(QRectF(margin - grow, margin - grow + 8, w + 2 * grow, h + 2 * grow),
                          radius + grow, radius + grow)
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(margin, margin, w, h), radius, radius)
    p.setClipPath(clip)
    if title:
        p.fillRect(QRectF(margin, margin, w, bar), QColor("#2d2d2d" if dark else "#e7e7e6"))
        p.setPen(QColor("#e8e8e8" if dark else "#2e3436"))
        f = QFont(p.font())
        f.setPointSizeF(10)
        f.setWeight(QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(margin, margin, w, bar), Qt.AlignCenter, title)
        p.setFont(QFont(f.family(), 11))
        p.drawText(QRectF(margin, margin, w - 14, bar), Qt.AlignRight | Qt.AlignVCenter, "–     ▢     ✕")
    p.drawPixmap(margin, margin + bar, pix)
    p.end()
    return img


def wait(ms: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main() -> int:
    seed_settings()
    OUT.mkdir(parents=True, exist_ok=True)
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(["wadesk"])
    app.setApplicationName("wadesk")
    app.setQuitOnLastWindowClosed(False)

    import wadesk.app as A
    from wadesk.window import MainWindow
    MainWindow.start = lambda self: None  # never contact WhatsApp; the demo page is used instead
    ctl = A.Application(app, minimized=False)
    w, page, settings = ctl.window, ctl.window.page, ctl.settings
    dark = lambda: ctl.tokens.dark

    def js(code):
        box, loop = {}, QEventLoop()
        page.runJavaScript(code, lambda r: (box.update(v=r), loop.quit()))
        loop.exec()
        return box.get("v")

    def save(img: QImage, name: str) -> None:
        img.save(str(OUT / name), "PNG")
        print(f"  wrote docs/images/{name} ({img.width()}x{img.height()})", flush=True)

    def shot_window(name: str) -> None:
        wait(300)
        save(framed(w.grab(), dark()), name)

    def hover(selector: str | None) -> None:
        x, y = (900, 700) if selector is None else json.loads(js(
            f"(()=>{{const r=document.querySelector('{selector}').getBoundingClientRect();"
            f"return JSON.stringify([r.x + r.width/2, r.y + r.height/2]);}})()"))
        ev = QMouseEvent(QEvent.MouseMove, QPointF(x, y), QPointF(x, y), Qt.NoButton, Qt.NoButton,
                         Qt.NoModifier)
        app.sendEvent(w.view.focusProxy(), ev)
        wait(500)

    w.resize(1180, 760)
    w.show()
    wait(800)
    page.setHtml((ROOT / "tools" / "demo_chat.html").read_text(encoding="utf-8"),
                 QUrl("https://web.whatsapp.com/"))
    wait(2500)
    w._hook_input_widget()

    print("main window", flush=True)
    shot_window("main-light.png")

    print("privacy blur", flush=True)
    settings.set("privacy_blur_list", True)
    wait(500)
    hover("#li2")
    shot_window("privacy-chat-list.png")
    settings.set("privacy_blur_chat", True)
    wait(500)
    hover("#main .message-in")
    shot_window("privacy-everything.png")
    settings.set("privacy_blur_list", False)
    settings.set("privacy_blur_chat", False)
    hover(None)

    print("dark theme", flush=True)
    settings.set("theme", "dark")
    wait(1200)
    shot_window("main-dark.png")

    print("menu", flush=True)
    w.menuBar().setVisible(True)
    wait(300)
    tools = next(a.menu() for a in w.menuBar().actions() if a.text() == "&Tools")
    tools.popup(w.mapToGlobal(QPoint(120, 40)))
    wait(400)
    save(framed(tools.grab(), dark(), title=None, margin=24, radius=10), "menu-tools.png")
    tools.hide()
    w.menuBar().setVisible(False)

    print("lock screen", flush=True)
    settings.set("theme", "light")
    wait(900)
    w.lock()
    wait(400)
    for _ in range(2):
        w.lock_screen.field.setText("0000")
        w.lock_screen._submit()
    wait(300)
    shot_window("lock-screen.png")
    w.lock_screen.field.setText(PIN)
    w.lock_screen._submit()
    wait(300)

    print("settings dialog", flush=True)
    settings.set("privacy_blur_list", True)
    dlg = SettingsDialog(settings, w)
    dlg.resize(780, 660)
    # The real mouse pointer may be resting over the dialog; don't let it tint a sidebar row.
    dlg.setStyleSheet("QListWidget#nav::item:hover:!selected { background: transparent; }")
    dlg.show()
    pages = {}
    for i in range(dlg.nav.count()):
        name = dlg.nav.item(i).text()
        dlg.nav.setCurrentRow(i)
        wait(250)
        if name in ("General", "Notifications", "Appearance", "Privacy", "Security"):
            pages[name] = framed(dlg.grab(), dark(), title=f"Settings – {name}")
            save(pages[name], f"settings-{name.lower()}.png")
    dlg.close()
    cols, scale = 2, 0.62
    cells = [pages[n].scaled(int(pages[n].width() * scale), int(pages[n].height() * scale),
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
             for n in ("General", "Notifications", "Privacy", "Security")]
    cw, ch = cells[0].width(), cells[0].height()
    sheet = QImage(cw * cols, ch * 2, QImage.Format_ARGB32_Premultiplied)
    sheet.fill(Qt.transparent)
    p = QPainter(sheet)
    for i, cell in enumerate(cells):
        p.drawImage((i % cols) * cw, (i // cols) * ch, cell)
    p.end()
    save(sheet, "settings-overview.png")

    print("tray icons", flush=True)
    items = [("Idle", 0, False), ("3 unread", 3, False), ("27 unread", 27, False),
             ("99+ unread", 120, False), ("Do Not Disturb", 5, True)]
    cell_w, ph = 170, 150
    strip = QImage(cell_w * len(items) + 40, ph + 40, QImage.Format_ARGB32_Premultiplied)
    strip.fill(Qt.transparent)
    p = QPainter(strip)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2b2e33"))
    p.drawRoundedRect(QRectF(20, 20, strip.width() - 40, ph), 14, 14)
    p.setPen(QColor("#d6d9de"))
    for i, (label, n, dnd) in enumerate(items):
        x = 20 + i * cell_w
        p.drawPixmap(x + (cell_w - 72) // 2, 44, make_icon(n, dnd).pixmap(72, 72))
        p.drawText(QRectF(x, 130, cell_w, 30), Qt.AlignCenter, label)
    p.end()
    save(strip, "tray-badges.png")
    save(render_base(256), "icon.png")

    print("done", flush=True)
    app.quit()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        import shutil
        shutil.rmtree(TMP, ignore_errors=True)
