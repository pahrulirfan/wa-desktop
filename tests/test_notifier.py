import pytest
from PySide6.QtCore import QObject, Signal

from wadesk import notifier, paths
from wadesk.settings import Settings


class FakeTray(QObject):
    messageClicked = Signal()

    def __init__(self):
        super().__init__()
        self.messages = []

    def showMessage(self, title, body, icon, msecs):  # noqa: N802 - Qt's name
        self.messages.append((title, body))

    def icon(self):
        return None


@pytest.fixture
def make(qapp, tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(paths, "CONFIG_DIR", tmp_path / "config")

    def build():
        tray = FakeTray()
        return notifier.Notifier(Settings(), tray), tray
    return build


@pytest.mark.parametrize("os_name", ["windows", "macos"])
def test_windows_and_macos_use_the_tray(force_os, make, os_name):
    force_os(os_name)
    n, tray = make()
    assert n.backend == "tray"
    n.send_test()
    assert tray.messages == [("WA Desktop", "Notifications are working 🎉")]


def test_linux_uses_notify_send_when_installed(force_os, make, monkeypatch):
    force_os("linux")
    monkeypatch.setattr(notifier.platform, "notifier_backend",
                        lambda: ("notify-send", "/usr/bin/notify-send"))
    n, _ = make()
    assert n.backend == "notify-send"


def test_linux_falls_back_to_the_tray(force_os, make, monkeypatch):
    force_os("linux")
    monkeypatch.setattr(notifier.platform.shutil, "which", lambda name: None)
    n, tray = make()
    assert n.backend == "tray"
    n.send_test()
    assert len(tray.messages) == 1


def test_clicking_a_tray_message_opens_the_chat(force_os, make):
    force_os("windows")
    n, tray = make()
    clicked = []
    n.activated.connect(lambda: clicked.append("window"))

    class FakeNotification:
        def click(self):
            clicked.append("chat")
    n._last = FakeNotification()
    tray.messageClicked.emit()
    assert clicked == ["window", "chat"]
    tray.messageClicked.emit()  # a second click only raises the window
    assert clicked == ["window", "chat", "window"]
