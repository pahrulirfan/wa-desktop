"""Main window: the WhatsApp web view plus menus, zoom, fullscreen and tray behaviour."""

import re
import time

from PySide6.QtCore import QByteArray, QEvent, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QMenu, QWidget

from . import APP_NAME, WA_URL
from .lock import LockScreen
from .settings import Settings
from .theme import Tokens
from .tray import base_pixmap
from .webpage import WaPage
from .widgets import StatusOverlay, Toast

ZOOM_MIN, ZOOM_MAX, ZOOM_STEP = 0.5, 2.0, 0.1
UNREAD_RE = re.compile(r"^\((\d+)\)")
_ACTIVITY_EVENTS = (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.KeyPress, QEvent.Wheel)

# Browser-style actions that make no sense in a desktop app.
_HIDDEN_ACTIONS = (
    QWebEnginePage.WebAction.Back, QWebEnginePage.WebAction.Forward,
    QWebEnginePage.WebAction.Reload, QWebEnginePage.WebAction.Stop,
    QWebEnginePage.WebAction.ViewSource, QWebEnginePage.WebAction.SavePage,
    QWebEnginePage.WebAction.InspectElement, QWebEnginePage.WebAction.OpenLinkInNewWindow,
    QWebEnginePage.WebAction.OpenLinkInNewTab, QWebEnginePage.WebAction.OpenLinkInThisWindow,
    QWebEnginePage.WebAction.OpenLinkInNewBackgroundTab,
)


class MainWindow(QMainWindow):
    unread_changed = Signal(int)
    quit_requested = Signal()
    settings_requested = Signal()
    about_requested = Signal()
    clear_cache_requested = Signal()
    lock_changed = Signal(bool)
    forgot_pin_requested = Signal()
    attention_changed = Signal(bool)  # True = the window is visible and active

    def __init__(self, settings: Settings, page: WaPage, tokens: Tokens, logo, tray=None):
        super().__init__()
        self.settings = settings
        self.page = page
        self.tray = tray
        self._quitting = False
        self._unread = 0
        self._alt_alone = False
        self._was_maximized = False
        self._input_widget = None
        self.locked = False
        self._last_activity = time.monotonic()
        self._retry_timer = QTimer(self, interval=10000)
        self._retry_timer.timeout.connect(self.reload)

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(420, 560)
        self.resize(1200, 800)

        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.view = QWebEngineView(self.container)
        self.view.setPage(page)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._context_menu)
        self.overlay = StatusOverlay(logo, tokens, self.container)
        self.toast = Toast(self.container)
        self.lock_screen = LockScreen(logo, tokens, settings, self.container)
        self.lock_screen.hide()
        self.lock_screen.unlocked.connect(self.unlock)
        self.lock_screen.forgot.connect(self.forgot_pin_requested)
        self._idle_timer = QTimer(self, interval=10_000)
        self._idle_timer.timeout.connect(self._check_idle)
        self._idle_timer.start()

        self._build_actions()
        self._build_menus()
        self.menuBar().setVisible(settings["show_menubar"])

        page.titleChanged.connect(self._on_title)
        page.loadStarted.connect(self._on_load_started)
        page.loadFinished.connect(self._on_load_finished)
        page.renderProcessTerminated.connect(self._on_crash)
        page.fullscreen_requested.connect(self._set_fullscreen)
        self.overlay.retry.connect(self.reload)
        settings.changed.connect(self._on_setting)

        self._restore_geometry()
        self.overlay.show_loading()

    # ---------- actions & menus ----------
    def _act(self, text, slot=None, shortcut=None, checkable=False) -> QAction:
        a = QAction(text, self)
        a.setCheckable(checkable)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
            a.setShortcutContext(Qt.WindowShortcut)
        if slot:
            a.triggered.connect(slot)
        self.addAction(a)
        return a

    def _build_actions(self) -> None:
        self.act_reload = self._act("Reload", self.reload, "Ctrl+R")
        self.addAction(self._act("Reload (F5)", self.reload, "F5"))
        self.act_fullscreen = self._act("Fullscreen", self.toggle_fullscreen, "F11", True)
        self.act_zoom_in = self._act("Zoom in", lambda: self.step_zoom(+ZOOM_STEP), "Ctrl++")
        self.addAction(self._act("Zoom in", lambda: self.step_zoom(+ZOOM_STEP), "Ctrl+="))
        self.act_zoom_out = self._act("Zoom out", lambda: self.step_zoom(-ZOOM_STEP), "Ctrl+-")
        self.act_zoom_reset = self._act("Actual size", lambda: self.set_zoom(1.0), "Ctrl+0")
        self.act_menubar = self._act("Show menu bar", self.toggle_menubar, "Ctrl+M", True)
        self.act_menubar.setChecked(self.settings["show_menubar"])
        self.act_dnd = self._act("Do Not Disturb", lambda c: self.settings.set("dnd", c),
                                 "Ctrl+Shift+D", True)
        self.act_dnd.setChecked(self.settings["dnd"])
        self.act_privacy = self._act("Blur chat list", lambda c: self.settings.set("privacy_blur_list", c),
                                     "Ctrl+Shift+B", True)
        self.act_privacy.setChecked(self.settings["privacy_blur_list"])
        self.act_lock = self._act("Lock now", self.lock, "Ctrl+L")
        self.act_lock.setEnabled(self.lock_available())
        self.act_settings = self._act("Settings…", self.settings_requested.emit, "Ctrl+,")
        self.act_about = self._act("About WA Desktop", self.about_requested.emit)
        self.act_clear = self._act("Clear cache", self.clear_cache_requested.emit)
        self.act_hide = self._act("Hide to tray", self.hide, "Ctrl+W")
        self.act_quit = self._act("Quit", self.quit_requested.emit, "Ctrl+Q")

    def _build_menus(self) -> None:
        mb = self.menuBar()
        m = mb.addMenu("&File")
        m.addActions([self.act_reload, self.act_hide])
        m.addSeparator()
        m.addAction(self.act_quit)
        m = mb.addMenu("&View")
        m.addActions([self.act_zoom_in, self.act_zoom_out, self.act_zoom_reset])
        m.addSeparator()
        m.addActions([self.act_fullscreen, self.act_menubar])
        m = mb.addMenu("&Tools")
        m.addActions([self.act_lock, self.act_privacy, self.act_dnd, self.act_settings])
        m.addSeparator()
        m.addAction(self.act_clear)
        m = mb.addMenu("&Help")
        m.addAction(self.act_about)

    def _context_menu(self, pos) -> None:
        menu: QMenu = self.view.createStandardContextMenu()
        for action in _HIDDEN_ACTIONS:
            menu.removeAction(self.page.action(action))
        if menu.isEmpty() or all(a.isSeparator() for a in menu.actions()):
            menu.deleteLater()
            return
        menu.popup(self.view.mapToGlobal(pos))

    # ---------- load cycle ----------
    def reload(self) -> None:
        self._retry_timer.stop()
        if self.page.url().isEmpty() or self.page.url().scheme() == "chrome-error":
            self.page.load(WA_URL)
        else:
            self.page.triggerAction(QWebEnginePage.WebAction.Reload)

    def start(self) -> None:
        self.page.grant_defaults()
        self.page.load(WA_URL)

    def _on_load_started(self) -> None:
        if not self.overlay.isVisible():
            return
        self.overlay.show_loading()
        self._keep_lock_on_top()

    def _on_load_finished(self, ok: bool) -> None:
        self._hook_input_widget()
        if ok:
            self._retry_timer.stop()
            self.view.setZoomFactor(self.settings["zoom"])
            self.overlay.fade_out()
        else:
            self.overlay.show_error("Can't connect",
                                    "Check your internet connection. Retrying automatically "
                                    "every 10 seconds.")
            self._keep_lock_on_top()
            self._retry_timer.start()

    def _on_crash(self, *_args) -> None:
        self.overlay.show_error("The page stopped responding", "Reloading…")
        self._keep_lock_on_top()
        QTimer.singleShot(800, lambda: self.page.load(WA_URL))

    # ---------- app lock ----------
    def lock_available(self) -> bool:
        return bool(self.settings["lock_enabled"] and self.settings["lock_hash"])

    def lock(self) -> None:
        if self.locked or not self.lock_available():
            return
        self.locked = True
        self.toast.suppressed = True
        self.toast.hide()
        self.view.setEnabled(False)
        self.act_settings.setEnabled(False)
        self.lock_screen.reset()
        self.lock_screen.setGeometry(self.container.rect())
        self.lock_screen.show()
        self.lock_screen.raise_()
        QTimer.singleShot(0, self.lock_screen.focus_field)
        self.lock_changed.emit(True)

    def unlock(self) -> None:
        if not self.locked:
            return
        self.locked = False
        self.lock_screen.hide()
        self.toast.suppressed = False
        self.view.setEnabled(True)
        self.act_settings.setEnabled(True)
        self.view.setFocus()
        self._last_activity = time.monotonic()
        self.lock_changed.emit(False)

    def _keep_lock_on_top(self) -> None:
        if self.locked:
            self.lock_screen.raise_()

    def _check_idle(self) -> None:
        minutes = self.settings["lock_auto_minutes"]
        if minutes > 0 and not self.locked and self.lock_available() \
                and time.monotonic() - self._last_activity > minutes * 60:
            self.lock()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.ActivationChange, QEvent.WindowStateChange):
            self.attention_changed.emit(self.isActiveWindow() and self.isVisible()
                                        and not self.isMinimized())

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._last_activity = time.monotonic()
        if self.locked:
            QTimer.singleShot(0, self.lock_screen.focus_field)

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self.attention_changed.emit(False)
        # Only when hidden to the tray (not spontaneous), not when minimised.
        if not event.spontaneous() and not self._quitting and self.settings["lock_on_hide"]:
            self.lock()

    # ---------- unread ----------
    def _on_title(self, title: str) -> None:
        m = UNREAD_RE.match(title)
        n = int(m.group(1)) if m else 0
        if n != self._unread:
            self._unread = n
            self.unread_changed.emit(n)
        self.setWindowTitle(f"({n}) {APP_NAME}" if n else APP_NAME)

    # ---------- zoom & fullscreen ----------
    def set_zoom(self, factor: float) -> None:
        factor = round(min(ZOOM_MAX, max(ZOOM_MIN, factor)), 2)
        self.view.setZoomFactor(factor)
        self.settings.set("zoom", factor)
        self.toast.popup(f"Zoom {round(factor * 100)}%", msecs=1200)

    def step_zoom(self, delta: float) -> None:
        self.set_zoom(self.view.zoomFactor() + delta)

    def toggle_fullscreen(self) -> None:
        self._set_fullscreen(not self.isFullScreen())

    def _set_fullscreen(self, on: bool) -> None:
        if on == self.isFullScreen():
            return
        if on:
            self._was_maximized = self.isMaximized()
            self.showFullScreen()
        else:
            self.showMaximized() if self._was_maximized else self.showNormal()
        self.act_fullscreen.setChecked(on)

    def toggle_menubar(self) -> None:
        visible = not self.menuBar().isVisible()
        self.menuBar().setVisible(visible)
        self.act_menubar.setChecked(visible)
        self.settings.set("show_menubar", visible)

    def _on_setting(self, key: str) -> None:
        if key == "dnd":
            self.act_dnd.setChecked(self.settings["dnd"])
        elif key == "show_menubar":
            self.menuBar().setVisible(self.settings["show_menubar"])
            self.act_menubar.setChecked(self.settings["show_menubar"])
        elif key == "zoom":
            self.view.setZoomFactor(self.settings["zoom"])
        elif key in ("lock_enabled", "lock_hash"):
            self.act_lock.setEnabled(self.lock_available())
        elif key == "privacy_blur_list":
            self.act_privacy.setChecked(self.settings["privacy_blur_list"])

    # ---------- show / hide ----------
    def show_and_raise(self) -> None:
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    def toggle_visibility(self) -> None:
        if self.isVisible() and self.isActiveWindow():
            self.hide()
        else:
            self.show_and_raise()

    def quit_for_real(self) -> None:
        self._quitting = True
        self._save_geometry()

    def _save_geometry(self) -> None:
        if not self.isFullScreen():
            self.settings.set("geometry", bytes(self.saveGeometry().toBase64()).decode())

    def _restore_geometry(self) -> None:
        raw = self.settings["geometry"]
        if raw:
            self.restoreGeometry(QByteArray.fromBase64(raw.encode()))

    def closeEvent(self, event) -> None:
        self._save_geometry()
        tray_ok = self.tray is not None and self.tray.isVisible()
        if not self._quitting and self.settings["close_to_tray"] and tray_ok:
            event.ignore()
            self.hide()
            if not self.settings["tray_hint_shown"]:
                self.settings.set("tray_hint_shown", True)
                self.tray.showMessage(APP_NAME, "The app keeps running in the system tray. "
                                      "Click its icon to open it again.",
                                      self.tray.icon(), 5000)
            return
        event.accept()
        self.quit_requested.emit()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.overlay.setGeometry(self.container.rect())
        self.view.setGeometry(self.container.rect())
        self.lock_screen.setGeometry(self.container.rect())
        self.toast.reposition()

    # ---------- event filter: Alt key, Ctrl+wheel ----------
    def _hook_input_widget(self) -> None:
        """Install the filter only on the web view's input widget (never application-wide)."""
        proxy = self.view.focusProxy()
        if proxy is not None and proxy is not self._input_widget:
            self._input_widget = proxy
            proxy.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        t = event.type()
        if t in _ACTIVITY_EVENTS:
            self._last_activity = time.monotonic()
        if t == QEvent.Wheel and event.modifiers() & Qt.ControlModifier:
            self.step_zoom(ZOOM_STEP if event.angleDelta().y() > 0 else -ZOOM_STEP)
            return True
        if t == QEvent.KeyPress:
            self._alt_alone = event.key() == Qt.Key_Alt and not event.isAutoRepeat()
        elif t == QEvent.KeyRelease and event.key() == Qt.Key_Alt and self._alt_alone \
                and not event.isAutoRepeat():
            self._alt_alone = False
            self.toggle_menubar()
        return False
