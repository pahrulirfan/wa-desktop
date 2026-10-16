"""Light and dark themes that match the colours of WhatsApp Web."""

import subprocess
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette


@dataclass(frozen=True)
class Tokens:
    dark: bool
    bg: str
    panel: str
    text: str
    muted: str
    border: str
    accent: str
    accent_hover: str
    hover: str
    danger: str


LIGHT = Tokens(False, "#f0f2f5", "#ffffff", "#111b21", "#667781", "#d1d7db",
               "#00a884", "#008f72", "#e9edef", "#ea0038")
DARK = Tokens(True, "#111b21", "#202c33", "#e9edef", "#8696a0", "#2a3942",
              "#00a884", "#06cf9c", "#2a3942", "#f15c6d")


def _gsettings(schema: str, key: str) -> str:
    try:
        out = subprocess.run(["gsettings", "get", schema, key], capture_output=True,
                             text=True, timeout=2)
        return out.stdout.strip().strip("'").lower() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def system_is_dark() -> bool:
    scheme = QGuiApplication.styleHints().colorScheme()
    if scheme != Qt.ColorScheme.Unknown:
        return scheme == Qt.ColorScheme.Dark
    if "dark" in _gsettings("org.gnome.desktop.interface", "color-scheme"):
        return True
    for schema in ("org.cinnamon.desktop.interface", "org.gnome.desktop.interface"):
        if "dark" in _gsettings(schema, "gtk-theme"):
            return True
    return False


def resolve(mode: str) -> Tokens:
    dark = system_is_dark() if mode == "system" else mode == "dark"
    return DARK if dark else LIGHT


def palette(t: Tokens) -> QPalette:
    p = QPalette()
    roles = {
        QPalette.Window: t.bg, QPalette.WindowText: t.text,
        QPalette.Base: t.panel, QPalette.AlternateBase: t.bg,
        QPalette.Text: t.text, QPalette.Button: t.panel, QPalette.ButtonText: t.text,
        QPalette.ToolTipBase: t.panel, QPalette.ToolTipText: t.text,
        QPalette.Highlight: t.accent, QPalette.HighlightedText: "#ffffff",
        QPalette.PlaceholderText: t.muted, QPalette.Link: t.accent,
    }
    for role, color in roles.items():
        p.setColor(role, QColor(color))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, QColor(t.muted))
    return p


def stylesheet(t: Tokens) -> str:
    return f"""
    QMenuBar {{ background: {t.panel}; color: {t.text}; border-bottom: 1px solid {t.border}; }}
    QMenuBar::item {{ padding: 6px 12px; background: transparent; }}
    QMenuBar::item:selected {{ background: {t.hover}; border-radius: 6px; }}
    QMenu {{ background: {t.panel}; color: {t.text}; border: 1px solid {t.border};
            border-radius: 10px; padding: 6px; }}
    QMenu::item {{ padding: 7px 26px 7px 14px; border-radius: 6px; }}
    QMenu::item:selected {{ background: {t.hover}; }}
    QMenu::item:disabled {{ color: {t.muted}; }}
    QMenu::separator {{ height: 1px; background: {t.border}; margin: 5px 8px; }}
    QToolTip {{ background: {t.panel}; color: {t.text}; border: 1px solid {t.border};
               padding: 4px 8px; }}

    QDialog#settings {{ background: {t.bg}; }}
    QListWidget#nav {{ background: {t.panel}; border: none; border-right: 1px solid {t.border};
                      outline: 0; padding: 10px 8px; }}
    QListWidget#nav::item {{ padding: 10px 14px; border-radius: 8px; color: {t.text};
                            margin-bottom: 2px; }}
    QListWidget#nav::item:hover {{ background: {t.hover}; }}
    QListWidget#nav::item:selected {{ background: {t.accent}; color: white; }}
    QLabel#pageTitle {{ font-size: 20px; font-weight: 600; color: {t.text}; }}
    QLabel#rowTitle {{ font-size: 14px; color: {t.text}; }}
    QLabel#rowDesc {{ font-size: 12px; color: {t.muted}; }}
    QFrame#row {{ background: {t.panel}; border: 1px solid {t.border}; border-radius: 12px; }}
    QScrollArea {{ border: none; background: transparent; }}

    QPushButton {{ background: {t.panel}; color: {t.text}; border: 1px solid {t.border};
                  border-radius: 8px; padding: 7px 16px; }}
    QPushButton:hover {{ background: {t.hover}; }}
    QPushButton#primary {{ background: {t.accent}; color: white; border: none; font-weight: 600; }}
    QPushButton#primary:hover {{ background: {t.accent_hover}; }}
    QPushButton#danger {{ color: {t.danger}; }}
    QComboBox, QSpinBox, QLineEdit {{ background: {t.bg}; color: {t.text};
        border: 1px solid {t.border}; border-radius: 8px; padding: 6px 10px; min-height: 20px; }}
    QComboBox QAbstractItemView {{ background: {t.panel}; color: {t.text};
        selection-background-color: {t.accent}; border: 1px solid {t.border}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {t.border}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: white; border: 1px solid {t.border};
                                 width: 16px; height: 16px; margin: -7px 0; border-radius: 9px; }}

    QFrame#toast {{ background: {"#2a3942" if t.dark else "#111b21"}; border-radius: 22px; }}
    QFrame#toast QLabel {{ color: #e9edef; font-size: 13px; }}
    QFrame#toast QPushButton {{ background: transparent; color: #25d366; border: none;
                               font-weight: 600; padding: 4px 8px; }}
    """


def apply(app, mode: str) -> Tokens:
    t = resolve(mode)
    app.setStyle("Fusion")
    app.setPalette(palette(t))
    app.setStyleSheet(stylesheet(t))
    hints = app.styleHints()
    if hasattr(hints, "setColorScheme"):
        hints.setColorScheme({"light": Qt.ColorScheme.Light, "dark": Qt.ColorScheme.Dark}
                             .get(mode, Qt.ColorScheme.Unknown))
    return t
