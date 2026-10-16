"""App lock with a PIN: hashing, lock screen and PIN dialogs."""

import hashlib
import hmac
import os
import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)

from .theme import Tokens

ITERATIONS = 200_000
MIN_LEN, MAX_LEN = 4, 32
FREE_ATTEMPTS = 5  # wrong attempts allowed before the lockout starts


def hash_pin(pin: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_pin(pin: str, stored: str) -> bool:
    try:
        algo, iterations, salt, expected = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(digest, bytes.fromhex(expected))
    except ValueError:
        return False


def check_new_pin(pin: str, confirm: str) -> str | None:
    """Return an error message, or None if the new PIN is valid."""
    if len(pin) < MIN_LEN:
        return f"The PIN must be at least {MIN_LEN} characters."
    if len(pin) > MAX_LEN:
        return f"The PIN must be at most {MAX_LEN} characters."
    if pin != confirm:
        return "The PINs do not match."
    return None


def lockout_seconds(failures: int) -> int:
    """0 for the first few attempts, then 30 s, 60 s, 120 s ... capped at 10 minutes."""
    if failures < FREE_ATTEMPTS:
        return 0
    return min(600, 30 * 2 ** (failures - FREE_ATTEMPTS))


class LockScreen(QWidget):
    """Full cover above the web view; input is restored only after the correct PIN."""

    unlocked = Signal()
    forgot = Signal()

    def __init__(self, logo, tokens: Tokens, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._bg = QColor(tokens.bg)
        self._failures = 0
        self._blocked_until = 0.0
        self._tick = QTimer(self, interval=500)
        self._tick.timeout.connect(self._update_block)

        self.logo = QLabel(alignment=Qt.AlignCenter)
        self.logo.setPixmap(logo)
        self.title = QLabel("WA Desktop is locked", alignment=Qt.AlignCenter)
        f = QFont(self.font())
        f.setPointSizeF(f.pointSizeF() + 5)
        f.setWeight(QFont.DemiBold)
        self.title.setFont(f)
        self.hint = QLabel("Enter your PIN to unlock", alignment=Qt.AlignCenter)
        self.field = QLineEdit(echoMode=QLineEdit.Password, alignment=Qt.AlignCenter)
        self.field.setMaxLength(MAX_LEN)
        self.field.setPlaceholderText("PIN")
        self.field.setFixedWidth(260)
        self.field.setStyleSheet("font-size: 20px; letter-spacing: 5px; padding: 9px 12px;")
        self.field.returnPressed.connect(self._submit)
        self.error = QLabel("", alignment=Qt.AlignCenter)
        self.error.setWordWrap(True)
        self.error.setMinimumHeight(34)
        self.error.setFixedWidth(320)
        self.button = QPushButton("Unlock")
        self.button.setObjectName("primary")
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setFixedWidth(260)
        self.button.clicked.connect(self._submit)
        self.forgot_btn = QPushButton("Forgot PIN?")
        self.forgot_btn.setFlat(True)
        self.forgot_btn.setCursor(Qt.PointingHandCursor)
        self.forgot_btn.clicked.connect(self.forgot)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(10)
        for w, space in ((self.logo, 4), (self.title, 0), (self.hint, 14), (self.field, 0),
                         (self.error, 0), (self.button, 0), (self.forgot_btn, 0)):
            lay.addWidget(w, 0, Qt.AlignCenter)
            if space:
                lay.addSpacing(space)
        self.apply_tokens(tokens)

    def apply_tokens(self, t: Tokens) -> None:
        self._bg = QColor(t.bg)
        self._danger = t.danger
        self.title.setStyleSheet(f"color: {t.text};")
        self.hint.setStyleSheet(f"color: {t.muted};")
        self.error.setStyleSheet(f"color: {t.danger};")
        self.forgot_btn.setStyleSheet(f"QPushButton {{ border: none; background: transparent; "
                                      f"color: {t.muted}; }} QPushButton:hover {{ color: {t.accent}; }}")
        self.update()

    def paintEvent(self, _e) -> None:
        QPainter(self).fillRect(self.rect(), self._bg)

    def reset(self) -> None:
        self.field.clear()
        if time.monotonic() >= self._blocked_until:
            self.error.setText("")
        self.focus_field()

    def focus_field(self) -> None:
        if self.field.isEnabled():
            self.field.setFocus()

    def keyPressEvent(self, event) -> None:
        event.accept()  # keystrokes must not leak to widgets underneath

    def _submit(self) -> None:
        if time.monotonic() < self._blocked_until:
            return
        pin = self.field.text()
        self.field.clear()
        if not pin:
            return
        if verify_pin(pin, self._settings["lock_hash"]):
            self._failures = 0
            self.error.setText("")
            self.unlocked.emit()
            return
        self._failures += 1
        wait = lockout_seconds(self._failures)
        if wait:
            self._blocked_until = time.monotonic() + wait
            self._tick.start()
            self._update_block()
        else:
            left = FREE_ATTEMPTS - self._failures
            self.error.setText(f"Wrong PIN. {left} attempt{'s' if left != 1 else ''} left before a lockout.")

    def _update_block(self) -> None:
        remaining = int(self._blocked_until - time.monotonic() + 0.99)
        blocked = remaining > 0
        self.field.setEnabled(not blocked)
        self.button.setEnabled(not blocked)
        if blocked:
            self.field.clear()
            self.error.setText(f"Too many wrong attempts. Try again in {remaining} s.")
        else:
            self._tick.stop()
            self.error.setText("")
            self.focus_field()


def request_pins(parent, title: str, text: str, labels: list[str], validate=None) -> list[str] | None:
    """Small dialog with one or more PIN fields. Returns their values, or None if cancelled."""
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setMinimumWidth(360)
    lay = QVBoxLayout(dlg)
    lay.setContentsMargins(22, 20, 22, 18)
    lay.setSpacing(8)
    heading = QLabel(title)
    heading.setObjectName("pageTitle")
    lay.addWidget(heading)
    desc = QLabel(text)
    desc.setObjectName("rowDesc")
    desc.setWordWrap(True)
    lay.addWidget(desc)
    lay.addSpacing(6)
    fields = []
    for label in labels:
        caption = QLabel(label)
        caption.setObjectName("rowTitle")
        edit = QLineEdit(echoMode=QLineEdit.Password)
        edit.setMaxLength(MAX_LEN)
        lay.addWidget(caption)
        lay.addWidget(edit)
        fields.append(edit)
    error = QLabel("")
    error.setWordWrap(True)
    error.setStyleSheet("color: #e5484d;")
    lay.addWidget(error)
    row = QHBoxLayout()
    row.addStretch(1)
    cancel = QPushButton("Cancel")
    ok = QPushButton("Save" if len(labels) > 1 else "Continue")
    ok.setObjectName("primary")
    ok.setDefault(True)
    row.addWidget(cancel)
    row.addWidget(ok)
    lay.addLayout(row)

    def accept() -> None:
        values = [f.text() for f in fields]
        problem = validate(values) if validate else None
        if problem:
            error.setText(problem)
            return
        dlg.accept()

    cancel.clicked.connect(dlg.reject)
    ok.clicked.connect(accept)
    for f in fields:
        f.returnPressed.connect(accept)
    fields[0].setFocus()
    if dlg.exec() != QDialog.Accepted:
        return None
    return [f.text() for f in fields]


def confirm_forgot(parent) -> bool:
    answer = QMessageBox.warning(
        parent, "Forgot PIN",
        "For security reasons a forgotten PIN cannot be recovered.\n\n"
        "The only way forward is to remove the WhatsApp session from this computer and turn "
        "the lock off. You will need to scan the QR code again.\n\nContinue?",
        QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
    return answer == QMessageBox.Yes
