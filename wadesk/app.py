"""Entry point: wires all components together and guarantees a single running instance."""

import argparse
import os
import signal
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWidgets import QApplication, QMenu

from . import APP_ID, APP_NAME, __version__, autostart, paths, platform, theme
from .dialogs import SettingsDialog, show_about
from .lock import confirm_forgot
from .notifier import Notifier
from .privacy import Privacy
from .settings import Settings
from .tray import Tray, base_pixmap
from .webpage import DownloadManager, WaPage, make_profile
from .window import MainWindow

SOCKET_NAME = platform.socket_name()


class QtApp(QApplication):
    """Marks the window as quitting before Qt closes it for a system quit request (macOS Dock
    "Quit", logout, SIGTERM), so that close-to-tray does not cancel the quit. Overriding event()
    only sees events sent to the application object itself, unlike an application-wide filter."""

    before_quit = None

    def event(self, e) -> bool:
        if e.type() == QEvent.Quit and self.before_quit is not None:
            self.before_quit()
        return super().event(e)


class Application(QObject):
    def __init__(self, app: QtApp, minimized: bool, smoke: bool = False):
        super().__init__(app)
        self.app = app
        self.socket_name = f"{SOCKET_NAME}-smoke-{os.getpid()}" if smoke else SOCKET_NAME
        self._started = time.monotonic()
        self._minimized = minimized
        self.settings = Settings()
        self.tokens = theme.apply(app, self.settings["theme"])

        self.profile = make_profile(self.settings, self)
        self.page = WaPage(self.profile, self)
        self.tray = Tray(self)
        self.window = MainWindow(self.settings, self.page, self.tokens, base_pixmap(88), self.tray)
        self.window.setWindowIcon(self.tray.refresh())

        self.privacy = Privacy(self.page, self.settings, self)
        self.window.attention_changed.connect(lambda active: self.privacy.set_away(not active))
        self.notifier = Notifier(self.settings, self.tray, self)
        self.profile.setNotificationPresenter(self.notifier.present)
        self.notifier.activated.connect(self.window.show_and_raise)
        self.notifier.is_locked = lambda: self.window.locked
        self._settings_dialog = None

        self.downloads = DownloadManager(self.profile, self.settings, self.window)
        self.downloads.finished.connect(self._download_done)
        self.downloads.failed.connect(
            lambda n: self.window.toast.popup(f"Download failed: {n}", msecs=4000))

        self._build_tray_menu()
        self._wire()
        self._start_server()
        if self.settings["autostart"] and not smoke:
            self._sync_autostart()  # the app may have moved since the entry was written

        if self.window.lock_available() and self.settings["lock_on_start"]:
            self.window.lock()

        if self.tray.isSystemTrayAvailable():
            self.tray.show()
        if not (minimized or self.settings["start_minimized"]) or not self.tray.isVisible():
            self.window.show()
        if not smoke:
            self.window.start()

    # ---------- tray ----------
    def _build_tray_menu(self) -> None:
        m: QMenu = self.tray.menu
        self.tray_unread = m.addAction("No new messages")
        self.tray_unread.setEnabled(False)
        m.addSeparator()
        m.addAction("Open WA Desktop", self.window.show_and_raise)
        self.tray_dnd = m.addAction("Do Not Disturb")
        self.tray_dnd.setCheckable(True)
        self.tray_dnd.setChecked(self.settings["dnd"])
        self.tray_dnd.toggled.connect(lambda c: self.settings.set("dnd", c))
        self.tray_lock = m.addAction("Lock now", self.window.lock)
        self.tray_lock.setVisible(self.window.lock_available())
        m.addAction("Settings…", self.open_settings)
        m.addSeparator()
        m.addAction("Quit", self.quit)
        self.tray.activated.connect(self._tray_activated)

    def _tray_activated(self, reason) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon as T
        if platform.is_macos():
            return  # a click on a menu bar icon opens its menu, which has "Open WA Desktop"
        if reason in (T.Trigger, T.DoubleClick):
            self.window.toggle_visibility()
        elif reason == T.MiddleClick:
            self.window.show_and_raise()

    # ---------- signal wiring ----------
    def _wire(self) -> None:
        w = self.window
        w.quit_requested.connect(self.quit)
        w.settings_requested.connect(self.open_settings)
        w.about_requested.connect(lambda: show_about(w))
        w.clear_cache_requested.connect(self.clear_cache)
        w.unread_changed.connect(self._unread)
        w.lock_changed.connect(self._lock_changed)
        w.forgot_pin_requested.connect(self.forgot_pin)
        self.settings.changed.connect(self._setting_changed)
        self.app.aboutToQuit.connect(self._cleanup)
        self.app.before_quit = self.window.quit_for_real
        # Follow the system's light/dark switch live (deferred: applying a theme touches the hints).
        self.app.styleHints().colorSchemeChanged.connect(
            lambda *_: QTimer.singleShot(0, self._follow_system_theme))
        if platform.is_macos():
            self.app.applicationStateChanged.connect(self._app_state_changed)

    def _unread(self, n: int) -> None:
        w_icon = self.tray.refresh(unread=n)
        self.window.setWindowIcon(w_icon)
        self.tray_unread.setText(f"{n} unread message{'s' if n != 1 else ''}" if n else "No new messages")

    def _setting_changed(self, key: str) -> None:
        if key == "dnd":
            self.tray_dnd.blockSignals(True)
            self.tray_dnd.setChecked(self.settings["dnd"])
            self.tray_dnd.blockSignals(False)
            self.window.setWindowIcon(self.tray.refresh(dnd=self.settings["dnd"]))
        elif key == "theme":
            self._apply_theme()
        elif key == "autostart":
            self._sync_autostart()
        elif key in ("lock_enabled", "lock_hash"):
            self.tray_lock.setVisible(self.window.lock_available())

    def _apply_theme(self) -> None:
        self.tokens = theme.apply(self.app, self.settings["theme"])
        self.window.overlay.apply_tokens(self.tokens)
        self.window.lock_screen.apply_tokens(self.tokens)
        # Chromium only re-reads the preferred colour scheme when its web preferences are
        # refreshed; touching any attribute does that, so the page follows the new theme live.
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, False)

    def _follow_system_theme(self) -> None:
        if self.settings["theme"] == "system" and theme.resolve("system") != self.tokens:
            self._apply_theme()

    def _sync_autostart(self) -> None:
        try:
            autostart.set_enabled(self.settings["autostart"])
        except OSError as e:
            self.window.toast.popup(f"Could not change launch at login: {e}", msecs=5000)

    def _app_state_changed(self, state) -> None:
        # macOS: clicking the Dock icon re-activates the app; bring the hidden window back.
        # Right after a hidden start (e.g. at login) the activation is not a click, so skip it.
        if state != Qt.ApplicationActive or self.window.isVisible():
            return
        if self._minimized and time.monotonic() - self._started < 3:
            return
        self.window.show_and_raise()

    # ---------- actions ----------
    def open_settings(self) -> None:
        if self.window.locked:  # settings (including log out) must not be reachable while locked
            self.window.show_and_raise()
            return
        dlg = SettingsDialog(self.settings, self.window)
        dlg.test_notification.connect(self.notifier.send_test)
        dlg.clear_cache.connect(self.clear_cache)
        dlg.logout.connect(self.logout)
        dlg.lock_now.connect(lambda: (dlg.reject(), self.window.lock()))
        self._settings_dialog = dlg
        dlg.exec()
        self._settings_dialog = None

    def _lock_changed(self, locked: bool) -> None:
        if locked and self._settings_dialog is not None:
            self._settings_dialog.reject()

    def forgot_pin(self) -> None:
        if not confirm_forgot(self.window):
            return
        self.settings.set("lock_enabled", False)
        self.settings.set("lock_hash", "")
        self.logout()
        self.window.unlock()

    def clear_cache(self) -> None:
        self.profile.clearHttpCache()
        self.window.toast.popup("Cache cleared", msecs=2000)

    def logout(self) -> None:
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearHttpCache()
        self.page.runJavaScript(
            "localStorage.clear(); sessionStorage.clear();"
            "indexedDB.databases().then(d => d.forEach(x => indexedDB.deleteDatabase(x.name)));"
            "navigator.serviceWorker.getRegistrations().then(r => r.forEach(x => x.unregister()));"
        )
        QTimer.singleShot(800, self.window.reload)

    def _download_done(self, path: str) -> None:
        name = os.path.basename(path)
        folder = os.path.dirname(path)
        if self.window.isVisible():
            self.window.toast.popup(f"Saved: {name}", "Show in folder",
                                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(folder)),
                                    msecs=6000)
        else:
            self.tray.showMessage(APP_NAME, f"Download complete: {name}", self.tray.icon(), 4000)

    def quit(self) -> None:
        self.window.quit_for_real()
        self.app.quit()

    def _cleanup(self) -> None:
        self.notifier.shutdown()
        self.tray.hide()
        self.settings.save()
        # Release the page before the interpreter exits to avoid Qt warnings.
        self.window.view.setPage(None)
        self.page.deleteLater()

    # ---------- single instance ----------
    def _start_server(self) -> None:
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        QLocalServer.removeServer(self.socket_name)
        self.server.listen(self.socket_name)
        self.server.newConnection.connect(self._on_connection)

    def _on_connection(self) -> None:
        sock = self.server.nextPendingConnection()
        if sock is not None:
            sock.disconnectFromServer()
        self.window.show_and_raise()


def _already_running() -> bool:
    sock = QLocalSocket()
    sock.connectToServer(SOCKET_NAME)
    if sock.waitForConnected(300):
        platform.allow_foreground_handoff()
        sock.write(b"show")
        sock.waitForBytesWritten(300)
        sock.disconnectFromServer()
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wadesk", description=f"{APP_NAME} — WhatsApp desktop client")
    parser.add_argument("--minimized", action="store_true",
                        help=f"start hidden in the {platform.tray_place()}")
    parser.add_argument("--smoke", action="store_true",
                        help="self-test: open the window with a local page, then exit (0 = passed)")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    args, qt_args = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    platform.restore_library_path()
    policy = platform.root_policy()
    if policy == "refuse":
        print(f"Please run {APP_NAME} as a normal user, not as root.", file=sys.stderr)
        return 1

    smoke_dir = None
    if args.smoke:  # never touch the real settings and session
        smoke_dir = tempfile.TemporaryDirectory(prefix="wadesk-smoke-", ignore_cleanup_errors=True)
        paths.use_root(Path(smoke_dir.name))
    paths.ensure_dirs()
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    if Settings.peek("disable_gpu"):
        flags += " --disable-gpu"
    if policy == "no-sandbox":
        flags += " --no-sandbox"
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = flags.strip()

    platform.set_app_user_model_id()
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QtApp([sys.argv[0], *qt_args])
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setDesktopFileName(APP_ID)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(base_pixmap(256)))

    if args.smoke:
        from .smoke import run
        code = run(app, lambda: Application(app, minimized=False, smoke=True))
        smoke_dir.cleanup()
        return code

    if _already_running():
        return 0

    controller = Application(app, args.minimized)  # noqa: F841 (keeps a reference alive)

    # Wake the interpreter periodically so that Ctrl+C in a terminal works.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    tick = QTimer()
    tick.start(500)
    tick.timeout.connect(lambda: None)
    return app.exec()
