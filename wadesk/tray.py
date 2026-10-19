"""System tray icon with an unread-message badge.

Linux and Windows show the coloured icon with a red badge. macOS shows a monochrome template
image in the menu bar (macOS tints it to match the bar) and the count as a Dock badge.
"""

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from . import APP_NAME, paths, platform

SIZES = (16, 22, 24, 32, 48, 64, 128)
TEMPLATE_SIZES = (16, 18, 22, 32, 36, 44)

# The speech bubble and handset of icon.svg, cropped to the bubble, for the macOS menu bar.
_VIEW = 'xmlns="http://www.w3.org/2000/svg" viewBox="38 38 180 180"'
_BUBBLE = (f'<svg {_VIEW}><path fill="#000" d="M128 46c-45 0-82 33-82 76 0 18 6 34 17 47l-8 40 '
           '41-14c10 4 21 6 32 6 45 0 82-33 82-76s-37-79-82-79z"/></svg>').encode()
_HANDSET = (f'<svg {_VIEW}><path fill="#000" transform="translate(86 79) scale(3.5)" '
            'd="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 '
            '2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 '
            '1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>'
            ).encode()


def render_base(size: int) -> QImage:
    img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    QSvgRenderer(str(paths.ICON_SVG)).render(p, QRectF(0, 0, size, size))
    p.end()
    return img


def base_pixmap(size: int) -> QPixmap:
    return QPixmap.fromImage(render_base(size))


def _faded(img: QImage) -> QImage:
    out = QImage(img.size(), QImage.Format_ARGB32_Premultiplied)
    out.fill(Qt.transparent)
    q = QPainter(out)
    q.setOpacity(0.45)
    q.drawImage(0, 0, img)
    q.end()
    return out


def make_icon(unread: int = 0, dnd: bool = False) -> QIcon:
    icon = QIcon()
    for size in SIZES:
        img = render_base(size)
        if dnd:
            img = _faded(img)
        if unread > 0:
            _draw_badge(img, unread, dnd)
        icon.addPixmap(QPixmap.fromImage(img))
    return icon


def render_template(size: int, unread: bool = False) -> QImage:
    """Black glyph on transparent: the bubble with the handset cut out, plus a dot when unread."""
    img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    rect = QRectF(0, 0, size, size)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(_BUBBLE)).render(p, rect)
    p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
    QSvgRenderer(QByteArray(_HANDSET)).render(p, rect)
    if unread:
        d = size * 0.42
        dot = QRectF(size - d, 0, d, d)
        p.setPen(Qt.NoPen)
        p.setBrush(Qt.black)
        p.drawEllipse(dot.adjusted(-size * 0.08, -size * 0.08, size * 0.08, size * 0.08))
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.drawEllipse(dot)
    p.end()
    return img


def make_template_icon(unread: int = 0, dnd: bool = False) -> QIcon:
    icon = QIcon()
    for size in TEMPLATE_SIZES:
        img = render_template(size, unread > 0)
        icon.addPixmap(QPixmap.fromImage(_faded(img) if dnd else img))
    icon.setIsMask(True)
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
        self._template = platform.is_macos()
        super().__init__(make_template_icon() if self._template else make_icon(), parent)
        self.setToolTip(APP_NAME)
        self.menu = QMenu()
        self.setContextMenu(self.menu)
        self._unread = 0
        self._dnd = False

    def refresh(self, unread: int | None = None, dnd: bool | None = None) -> QIcon:
        """Update the tray icon and the native badge; returns the icon for the window."""
        if unread is not None:
            self._unread = unread
        if dnd is not None:
            self._dnd = dnd
        icon = make_icon(self._unread, self._dnd)
        self.setIcon(make_template_icon(self._unread, self._dnd) if self._template else icon)
        if not platform.is_linux():
            # Windows: overlay icon on the taskbar button; macOS: the red Dock badge. The window
            # icon then stays plain, otherwise the taskbar would show the count twice.
            QGuiApplication.instance().setBadgeNumber(self._unread)
            if self._unread:
                icon = make_icon(0, self._dnd)
        tip = APP_NAME
        if self._unread:
            tip += f" — {self._unread} unread message{'s' if self._unread != 1 else ''}"
        if self._dnd:
            tip += " (Do Not Disturb)"
        self.setToolTip(tip)
        return icon
