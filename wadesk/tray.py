"""System tray icon with an unread-message badge."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from . import APP_NAME, paths

SIZES = (16, 22, 24, 32, 48, 64, 128)


def render_base(size: int) -> QImage:
    img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    QSvgRenderer(str(paths.ICON_SVG)).render(p, QRectF(0, 0, size, size))
    p.end()
    return img


def base_pixmap(size: int) -> QPixmap:
    return QPixmap.fromImage(render_base(size))


def make_icon(unread: int = 0, dnd: bool = False) -> QIcon:
    icon = QIcon()
    for size in SIZES:
        img = render_base(size)
        if dnd:
            faded = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
            faded.fill(Qt.transparent)
            q = QPainter(faded)
            q.setOpacity(0.45)
            q.drawImage(0, 0, img)
            q.end()
            img = faded
        if unread > 0:
            _draw_badge(img, unread, dnd)
        icon.addPixmap(QPixmap.fromImage(img))
    return icon


def _draw_badge(img: QImage, count: int, muted: bool) -> None:
    size = img.width()
    text = "99+" if count > 99 else str(count)
    d = size * (0.62 if size <= 24 else 0.5)
    w = d if len(text) == 1 else d * (1.25 if len(text) == 2 else 1.6)
    rect = QRectF(size - w, size - d, w, d)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#7b8794" if muted else "#ef4444"))
    p.drawRoundedRect(rect, d / 2, d / 2)
    f = QFont()
    f.setBold(True)
    f.setPixelSize(max(6, int(d * (0.62 if len(text) == 1 else 0.52))))
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(rect, Qt.AlignCenter, text)
    p.end()


class Tray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(make_icon(), parent)
        self.setToolTip(APP_NAME)
        self.menu = QMenu()
        self.setContextMenu(self.menu)
        self._unread = 0
        self._dnd = False

    def refresh(self, unread: int | None = None, dnd: bool | None = None) -> QIcon:
        if unread is not None:
            self._unread = unread
        if dnd is not None:
            self._dnd = dnd
        icon = make_icon(self._unread, self._dnd)
        self.setIcon(icon)
        tip = APP_NAME
        if self._unread:
            tip += f" — {self._unread} unread message{'s' if self._unread != 1 else ''}"
        if self._dnd:
            tip += " (Do Not Disturb)"
        self.setToolTip(tip)
        return icon
