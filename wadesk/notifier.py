"""Native desktop notifications. Clicking one opens the window and the related chat.

Linux uses notify-send (with a click action); Windows and macOS, or Linux without notify-send,
use the tray icon's notification balloon / Notification Center message.
"""

import os
from itertools import count

from PySide6.QtCore import QObject, QProcess, Signal
from PySide6.QtGui import QIcon, QPixmap

from . import APP_ID, APP_NAME, paths, platform
from .settings import Settings


class Notifier(QObject):
    activated = Signal()  # the user clicked a notification

    def __init__(self, settings: Settings, tray, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._tray = tray
        self._ids = count(1)
        self._live: dict[int, tuple] = {}  # id -> (QProcess, notification, icon file)
        self.backend, self._send = platform.notifier_backend()
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
        image = notification.icon() if not locked else None
        self._dispatch(nid, title, body, image, notification)

    def send_test(self) -> None:
        self._dispatch(next(self._ids), APP_NAME, "Notifications are working 🎉", None, None)

    def _dispatch(self, nid: int, title: str, body: str, image, notification) -> None:
        has_image = image is not None and not image.isNull()
        if self._send:
            icon_file = ""
            if has_image:
                icon_file = str(self._icon_dir / f"{nid}.png")
                if not image.save(icon_file, "PNG"):
                    icon_file = ""
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
            # Clicking the message (Qt's messageClicked) opens the chat of the latest notification.
            self._last = notification
            icon = QIcon(QPixmap.fromImage(image)) if has_image else self._tray.icon()
            self._tray.showMessage(title, body, icon, 8000)

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
