"""Custom UI components: toggle switch, status overlay (loading/error) and toast."""

from PySide6.QtCore import (Property, QEasingCurve, QPropertyAnimation, QRectF, Qt, QTimer,
                            Signal)
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QPen
from PySide6.QtWidgets import (QAbstractButton, QFrame, QGraphicsOpacityEffect, QHBoxLayout,
                               QLabel, QPushButton, QVBoxLayout, QWidget)

from .theme import Tokens


class ToggleSwitch(QAbstractButton):
    """iOS/Material-style switch with a smooth animation."""

    def __init__(self, checked: bool = False, accent: str = "#00a884", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(46, 26)
        self._accent = QColor(accent)
        self._pos = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"position", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.toggled.connect(self._animate)

    def set_checked_silently(self, checked: bool) -> None:
        """Change the state without emitting toggled (and without animation)."""
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)
        self._anim.stop()
        self._pos = 1.0 if checked else 0.0
        self.update()

    def _animate(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def _get_position(self) -> float:
        return self._pos

    def _set_position(self, value: float) -> None:
        self._pos = value
        self.update()

    position = Property(float, _get_position, _set_position)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        dark = self.palette().color(QPalette.Window).lightness() < 128
        off = QColor("#4b5d68" if dark else "#aab6bd")
        track = QColor(
            int(off.red() + (self._accent.red() - off.red()) * self._pos),
            int(off.green() + (self._accent.green() - off.green()) * self._pos),
            int(off.blue() + (self._accent.blue() - off.blue()) * self._pos),
        )
        if not self.isEnabled():
            track.setAlpha(110)
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(self.rect(), 13, 13)
        d = self.height() - 6
        x = 3 + (self.width() - d - 6) * self._pos
        p.setBrush(QColor("white"))
        p.drawEllipse(QRectF(x, 3, d, d))


class Spinner(QWidget):
    def __init__(self, color: str = "#00a884", size: int = 44, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def _tick(self) -> None:
        self._angle = (self._angle - 7) % 360
        self.update()

    def showEvent(self, _e) -> None:
        self._timer.start()

    def hideEvent(self, _e) -> None:
        self._timer.stop()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self._color, 4, Qt.SolidLine, Qt.RoundCap)
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)
        track = QColor(self._color)
        track.setAlpha(45)
        p.setPen(QPen(track, 4))
        p.drawEllipse(rect)
        p.setPen(pen)
        p.drawArc(rect, self._angle * 16, 110 * 16)


class StatusOverlay(QWidget):
    """Full-size cover above the web view: a spinner while loading, a retry button on failure."""

    retry = Signal()

    def __init__(self, logo, tokens: Tokens, parent=None):
        super().__init__(parent)
        self._bg = QColor(tokens.bg)
        self._effect = None

        self.logo = QLabel(alignment=Qt.AlignCenter)
        self.logo.setPixmap(logo)
        self.title = QLabel(alignment=Qt.AlignCenter)
        f = QFont(self.font())
        f.setPointSizeF(f.pointSizeF() + 5)
        f.setWeight(QFont.DemiBold)
        self.title.setFont(f)
        self.detail = QLabel(alignment=Qt.AlignCenter)
        self.detail.setWordWrap(True)
        self.detail.setMinimumWidth(340)
        self.detail.setMaximumWidth(420)
        self.spinner = Spinner(tokens.accent)
        self.button = QPushButton("Try again")
        self.button.setObjectName("primary")
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setMinimumWidth(140)
        self.button.clicked.connect(self.retry)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(12)
        lay.addWidget(self.logo, 0, Qt.AlignCenter)
        lay.addSpacing(6)
        lay.addWidget(self.title, 0, Qt.AlignCenter)
        lay.addWidget(self.detail, 0, Qt.AlignCenter)
        lay.addSpacing(10)
        lay.addWidget(self.spinner, 0, Qt.AlignCenter)
        lay.addWidget(self.button, 0, Qt.AlignCenter)
        self.apply_tokens(tokens)

    def apply_tokens(self, t: Tokens) -> None:
        self._bg = QColor(t.bg)
        self.title.setStyleSheet(f"color: {t.text};")
        self.detail.setStyleSheet(f"color: {t.muted};")
        self.spinner.set_color(t.accent)
        self.update()

    def paintEvent(self, _e) -> None:
        QPainter(self).fillRect(self.rect(), self._bg)

    def _reset_fade(self) -> None:
        if self._effect is not None:
            self.setGraphicsEffect(None)
            self._effect = None

    def show_loading(self, text: str = "Connecting to WhatsApp…") -> None:
        self._reset_fade()
        self.title.setText("WA Desktop")
        self.detail.setText(text)
        self.spinner.show()
        self.button.hide()
        self._cover()

    def show_error(self, title: str, detail: str) -> None:
        self._reset_fade()
        self.title.setText(title)
        self.detail.setText(detail)
        self.spinner.hide()
        self.button.show()
        self._cover()

    def _cover(self) -> None:
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()

    def fade_out(self) -> None:
        if not self.isVisible():
            return
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        anim = QPropertyAnimation(self._effect, b"opacity", self)
        anim.setDuration(260)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self._after_fade)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def _after_fade(self) -> None:
        # If a new error appeared during the fade, keep the overlay visible.
        if self._effect is not None:
            self.hide()
            self._reset_fade()


class Toast(QFrame):
    """Small floating notice at the bottom of the window that disappears on its own."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("toast")
        self._label = QLabel()
        self._button = QPushButton()
        self._button.setCursor(Qt.PointingHandCursor)
        self._callback = None
        self.suppressed = False  # True while the app is locked: show nothing
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 9, 12, 9)
        lay.addWidget(self._label)
        lay.addWidget(self._button)
        self._button.clicked.connect(self._on_action)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(200)
        self._fading_out = False
        self._anim.finished.connect(self._on_anim_finished)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        self.hide()

    def popup(self, text: str, action: str | None = None, callback=None, msecs: int = 3500) -> None:
        if self.suppressed:
            return
        self._label.setText(text)
        self._callback = callback
        self._button.setVisible(bool(action))
        self._button.setText(action or "")
        self.adjustSize()
        self.reposition()
        self._anim.stop()
        self._fading_out = False
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(1.0)
        self.show()
        self.raise_()
        self._anim.start()
        self._timer.start(msecs)

    def reposition(self) -> None:
        p = self.parentWidget()
        self.move((p.width() - self.width()) // 2, p.height() - self.height() - 28)

    def _fade_out(self) -> None:
        self._fading_out = True
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _on_anim_finished(self) -> None:
        if self._fading_out:
            self.hide()

    def _on_action(self) -> None:
        cb, self._callback = self._callback, None
        self.hide()
        if cb:
            cb()
