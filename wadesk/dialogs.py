"""Settings dialog (sidebar + pages) and the About box."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QMessageBox, QPushButton, QScrollArea,
                               QSlider, QStackedWidget, QVBoxLayout, QWidget)

from . import APP_NAME, __version__, paths
from .lock import check_new_pin, hash_pin, request_pins, verify_pin
from .tray import base_pixmap
from .widgets import ToggleSwitch


class Row(QFrame):
    """One settings row: title + description on the left, control on the right."""

    def __init__(self, title: str, desc: str, control: QWidget):
        super().__init__()
        self.setObjectName("row")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        text = QVBoxLayout()
        text.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("rowTitle")
        text.addWidget(t)
        if desc:
            d = QLabel(desc)
            d.setObjectName("rowDesc")
            d.setWordWrap(True)
            text.addWidget(d)
        lay.addLayout(text, 1)
        lay.addSpacing(16)
        lay.addWidget(control, 0, Qt.AlignVCenter)


class SettingsDialog(QDialog):
    test_notification = Signal()
    clear_cache = Signal()
    logout = Signal()
    autostart_changed = Signal(bool)
    lock_now = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.s = settings
        self.setObjectName("settings")
        self.setWindowTitle("Settings")
        self.resize(780, 540)
        self.setMinimumSize(640, 440)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(190)
        self.stack = QStackedWidget()

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.nav)
        root.addWidget(self.stack, 1)

        self._page("General", self._general())
        self._page("Notifications", self._notifications())
        self._page("Appearance", self._appearance())
        self._page("Privacy", self._privacy())
        self._page("Security", self._security())
        self._page("Downloads", self._downloads())
        self._page("Advanced", self._advanced())
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)

    # --- helper ---
    def _page(self, name: str, rows: list[QWidget]) -> None:
        self.nav.addItem(name)
        self.nav.item(self.nav.count() - 1).setSizeHint(QSize(0, 42))
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(10)
        title = QLabel(name)
        title.setObjectName("pageTitle")
        lay.addWidget(title)
        lay.addSpacing(6)
        for r in rows:
            lay.addWidget(r)
        lay.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        self.stack.addWidget(scroll)

    def _toggle(self, key: str, on_change=None) -> ToggleSwitch:
        sw = ToggleSwitch(self.s[key])

        def changed(v):
            self.s.set(key, v)
            if on_change:
                on_change(v)
        sw.toggled.connect(changed)
        return sw

    @staticmethod
    def _button(text: str, slot, name: str = "") -> QPushButton:
        b = QPushButton(text)
        if name:
            b.setObjectName(name)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(slot)
        return b

    # --- pages ---
    def _general(self):
        return [
            Row("Close to tray", "The ✕ button only hides the window; WhatsApp keeps receiving "
                "messages in the background.", self._toggle("close_to_tray")),
            Row("Start hidden", "On launch, go straight to the tray without showing the "
                "window.", self._toggle("start_minimized")),
            Row("Launch at login", "Start automatically when you log in to your desktop.",
                self._toggle("autostart", self.autostart_changed.emit)),
        ]

    def _notifications(self):
        return [
            Row("Desktop notifications", "Show incoming messages as system notifications.",
                self._toggle("notifications")),
            Row("Show message preview", "When off, notifications only say \"New message\" "
                "without the sender or text.", self._toggle("notification_preview")),
            Row("Do Not Disturb", "Silence all notifications for now (Ctrl+Shift+D).",
                self._toggle("dnd")),
            Row("Test notification", "Send a test notification to make sure everything works.",
                self._button("Send test", self.test_notification.emit)),
        ]

    def _appearance(self):
        theme = QComboBox()
        for label, value in (("Follow system", "system"), ("Light", "light"), ("Dark", "dark")):
            theme.addItem(label, value)
        theme.setCurrentIndex(max(0, theme.findData(self.s["theme"])))
        theme.currentIndexChanged.connect(lambda: self.s.set("theme", theme.currentData()))

        zoom = QWidget()
        zl = QHBoxLayout(zoom)
        zl.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(50, 200)
        slider.setSingleStep(10)
        slider.setFixedWidth(170)
        slider.setValue(round(self.s["zoom"] * 100))
        label = QLabel(f"{slider.value()}%")
        label.setMinimumWidth(42)
        slider.valueChanged.connect(lambda v: (label.setText(f"{v}%"), self.s.set("zoom", v / 100)))
        self.s.changed.connect(lambda k: k == "zoom" and slider.setValue(round(self.s["zoom"] * 100)))
        zl.addWidget(slider)
        zl.addWidget(label)
        return [
            Row("Theme", "Sets the look of the app and of WhatsApp Web itself.", theme),
            Row("Zoom", "Make WhatsApp larger or smaller (Ctrl + / Ctrl -).", zoom),
            Row("Menu bar", "Show the menu bar above the window. Press Alt or Ctrl+M at any time.",
                self._toggle("show_menubar")),
        ]

    def _privacy(self):
        level = QComboBox()
        for label, px in (("Light", 4), ("Medium", 8), ("Strong", 14), ("Maximum", 22)):
            level.addItem(label, px)
        level.setCurrentIndex(max(0, level.findData(self.s["privacy_blur_level"])))
        level.currentIndexChanged.connect(lambda: self.s.set("privacy_blur_level", level.currentData()))
        note = QLabel("Blur only covers what is shown on this screen and disappears when you hover over "
                      "a row or open the chat. It relies on the structure of the WhatsApp Web page and "
                      "may need adjusting if WhatsApp changes its layout.")
        note.setObjectName("rowDesc")
        note.setWordWrap(True)
        return [
            Row("Blur chat list", "Names, photos and message previews in the chat list are blurred. "
                "Hover over a row to reveal it (Ctrl+Shift+B).",
                self._toggle("privacy_blur_list")),
            Row("Blur open conversation", "Messages and the name in the open chat are blurred too; "
                "hover over a message to read it.", self._toggle("privacy_blur_chat")),
            Row("Blur when window is inactive", "Everything is blurred while you work in another "
                "application.", self._toggle("privacy_blur_away")),
            Row("Blur strength", "How strongly the content is blurred.", level),
            note,
        ]

    # --- security: PIN lock ---
    def _lock_on(self) -> bool:
        return bool(self.s["lock_enabled"] and self.s["lock_hash"])

    def _refresh_lock_controls(self) -> None:
        on = self._lock_on()
        for w in (self.change_btn, self.now_btn, self.auto_combo, self.hide_switch, self.start_switch):
            w.setEnabled(on)

    def _security(self):
        on = self._lock_on()
        self.lock_switch = ToggleSwitch(on)
        self.lock_switch.toggled.connect(self._toggle_lock)
        self.change_btn = self._button("Change PIN…", self._change_pin)
        self.now_btn = self._button("Lock now", self.lock_now.emit)
        self.auto_combo = QComboBox()
        for label, minutes in (("Never", 0), ("1 minute", 1), ("5 minutes", 5),
                               ("15 minutes", 15), ("30 minutes", 30), ("1 hour", 60)):
            self.auto_combo.addItem(label, minutes)
        self.auto_combo.setCurrentIndex(max(0, self.auto_combo.findData(self.s["lock_auto_minutes"])))
        self.auto_combo.currentIndexChanged.connect(
            lambda: self.s.set("lock_auto_minutes", self.auto_combo.currentData()))
        self.hide_switch = self._toggle("lock_on_hide")
        self.start_switch = self._toggle("lock_on_start")
        self._refresh_lock_controls()
        note = QLabel("The PIN covers the window and disables input to WhatsApp. It is not encryption: "
                      "messages are still received in the background (notifications hide the sender "
                      "and text while locked) and the session files on disk are not encrypted. A "
                      "forgotten PIN can only be resolved by removing the session and scanning the "
                      "QR code again.")
        note.setObjectName("rowDesc")
        note.setWordWrap(True)
        return [
            Row("PIN lock", "Ask for a PIN to open the app.", self.lock_switch),
            Row("Change PIN", "Replace the PIN currently in use.", self.change_btn),
            Row("Lock now", "Lock the app immediately (Ctrl+L).", self.now_btn),
            Row("Auto-lock", "Lock after there has been no activity in this window.", self.auto_combo),
            Row("Lock when hidden", "Lock whenever the window is closed to the tray.", self.hide_switch),
            Row("Lock on launch", "Ask for the PIN every time WA Desktop starts.", self.start_switch),
            note,
        ]

    def _toggle_lock(self, on: bool) -> None:
        if on:
            pins = request_pins(self, "Create PIN",
                                "Use digits or letters, at least 4 characters. A forgotten PIN cannot be recovered.",
                                ["New PIN", "Repeat PIN"], lambda v: check_new_pin(v[0], v[1]))
            if pins is None:
                self.lock_switch.set_checked_silently(False)
                return
            self.s.set("lock_hash", hash_pin(pins[0]))
            self.s.set("lock_enabled", True)
        else:
            pins = request_pins(self, "Turn off lock", "Enter your current PIN to turn the lock off.",
                                ["Current PIN"], self._check_current)
            if pins is None:
                self.lock_switch.set_checked_silently(True)
                return
            self.s.set("lock_enabled", False)
            self.s.set("lock_hash", "")
        self._refresh_lock_controls()

    def _check_current(self, values) -> str | None:
        return None if verify_pin(values[0], self.s["lock_hash"]) else "The current PIN is wrong."

    def _change_pin(self) -> None:
        def validate(v):
            return self._check_current(v) or check_new_pin(v[1], v[2])
        pins = request_pins(self, "Change PIN", "Enter your current PIN, then a new one.",
                            ["Current PIN", "New PIN", "Repeat new PIN"], validate)
        if pins is not None:
            self.s.set("lock_hash", hash_pin(pins[1]))

    def _downloads(self):
        self.dir_label = QLabel(str(self.s.download_path))
        self.dir_label.setObjectName("rowDesc")
        holder = QWidget()
        hl = QHBoxLayout(holder)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self._button("Change…", self._choose_dir))
        return [
            Row("Download folder", str(self.s.download_path), holder),
            Row("Ask where to save", "Show a save dialog for every file.",
                self._toggle("ask_download_location")),
        ]

    def _choose_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose download folder", str(self.s.download_path))
        if d:
            self.s.set("download_dir", d)
            self.sender().parent().parent().findChild(QLabel, "rowDesc").setText(d)

    def _advanced(self):
        ua = QLineEdit(self.s["user_agent"])
        ua.setPlaceholderText("Automatic (recommended)")
        ua.setMinimumWidth(260)
        ua.editingFinished.connect(lambda: self.s.set("user_agent", ua.text().strip()))
        return [
            Row("Disable GPU acceleration", "Turn on only if the window flickers or stays "
                "blank. Requires a restart.", self._toggle("disable_gpu")),
            Row("Custom user agent", "Use if WhatsApp rejects the browser. Requires a restart.", ua),
            Row("Clear cache", "Delete the network cache. Your login is not affected.",
                self._button("Clear", self.clear_cache.emit)),
            Row("Data folder", str(paths.DATA_DIR),
                self._button("Open", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(paths.DATA_DIR))))),
            Row("Log out", "Remove the session from this computer; you will need to scan the QR "
                "code again. You can also unlink the device from your phone (Linked devices).",
                self._button("Log out and delete session", self._confirm_logout, "danger")),
        ]

    def _confirm_logout(self) -> None:
        ok = QMessageBox.question(self, "Log out",
                                  "Remove the WhatsApp session from this computer?\nYou will need to scan the QR "
                                  "code again to sign in.")
        if ok == QMessageBox.Yes:
            self.logout.emit()


def show_about(parent) -> None:
    box = QMessageBox(parent)
    box.setWindowTitle("About")
    box.setIconPixmap(base_pixmap(72))
    box.setText(f"<h3>{APP_NAME} {__version__}</h3>")
    box.setInformativeText(
        "An <b>unofficial</b> desktop client for WhatsApp Web, built with PySide6 "
        "(Qt WebEngine).<br><br>"
        "Not affiliated with WhatsApp LLC / Meta. Your messages stay end-to-end encrypted and "
        "never pass through a third-party server.<br><br>"
        "<b>Shortcuts:</b> Ctrl+, Settings · Ctrl+L Lock · Ctrl+Shift+B Blur chat list · "
        "Ctrl+Shift+D Do Not Disturb · Ctrl+± Zoom · F11 Fullscreen · Alt Menu · "
        "Ctrl+W Hide · Ctrl+Q Quit")
    box.exec()
