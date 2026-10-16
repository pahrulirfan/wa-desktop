"""Native desktop notifications. Clicking one opens the window and the related chat."""

import shutil
from itertools import count

from PySide6.QtCore import QObject, QProcess, Signal

from . import APP_ID, APP_NAME, paths
from .settings import Settings


class Notifier(QObject):
    activated = Signal()  # the user clicked a notification

    def __init__(self, settings: Settings, tray, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._tray = tray
        self._ids = count(1)
        self._live: dict[int, tuple] = {}  # id -> (QProcess, notification, icon file)
        self._send = shutil.which("notify-send")
        self._icon_dir = paths.CACHE_DIR / "notif"
        self._icon_dir.mkdir(parents=True, exist_ok=True)
        self._app_icon = str(paths.ICON_SVG)
        self._last = None
        self.is_locked = lambda: False  # replaced by Application
        tray.messageClicked.connect(self._tray_clicked)

    # --- called by QWebEngineProfile.setNotificationPresenter ---
    def present(self, notification) -> None:
        if not self._settings["notifications"] or self._settings["dnd"]:
            notification.close()
            return
        notification.show()
        locked = self.is_locked()
        title = APP_NAME if locked else (notification.title() or APP_NAME)
        body = notification.message() if self._settings["notification_preview"] and not locked \
            else "New message"
        nid = next(self._ids)
        icon_file = ""
        image = notification.icon()
        if not image.isNull() and not locked:
            icon_file = str(self._icon_dir / f"{nid}.png")
            if not image.save(icon_file, "PNG"):
                icon_file = ""
        self._dispatch(nid, title, body, icon_file, notification)

    def send_test(self) -> None:
        self._dispatch(next(self._ids), APP_NAME, "Notifications are working 🎉", "", None)

    def _dispatch(self, nid: int, title: str, body: str, icon_file: str, notification) -> None:
        if self._send:
            proc = QProcess(self)
            proc.setProgram(self._send)
            proc.setArguments([
                "-a", APP_NAME, "-i", icon_file or self._app_icon, "-c", "im.received",
                "-h", f"string:desktop-entry:{APP_ID}", "-t", "8000",
                "-A", "default=Open", "-w", "--", title, body,
            ])
            proc.finished.connect(lambda *_: self._finished(nid))
            self._live[nid] = (proc, notification, icon_file)
            proc.start()
        else:
            self._last = notification
            self._tray.showMessage(title, body, self._tray.icon(), 8000)

    def _finished(self, nid: int) -> None:
        entry = self._live.pop(nid, None)
        if not entry:
            return
        proc, notification, icon_file = entry
        clicked = bytes(proc.readAllStandardOutput()).decode(errors="ignore").strip() == "default"
        if clicked:
            self.activated.emit()
            if notification is not None:
                notification.click()
        elif notification is not None:
            notification.close()
        proc.deleteLater()
        if icon_file:
            try:
                import os
                os.unlink(icon_file)
            except OSError:
                pass

    def _tray_clicked(self) -> None:
        self.activated.emit()
        if self._last is not None:
            self._last.click()
            self._last = None

    def shutdown(self) -> None:
        live, self._live = self._live, {}
        for proc, *_ in live.values():
            proc.finished.disconnect()
            proc.kill()
            proc.waitForFinished(500)
