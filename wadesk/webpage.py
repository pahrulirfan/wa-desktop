"""Profile, page, permissions and downloads for WhatsApp Web in QtWebEngine."""

import re
from pathlib import Path

from PySide6.QtCore import QLocale, QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import (QWebEngineDownloadRequest, QWebEnginePage,
                                     QWebEnginePermission as P, QWebEngineProfile)
from PySide6.QtWidgets import QFileDialog

from . import APP_ID, paths
from .settings import Settings

INTERNAL_HOSTS = {"web.whatsapp.com", "static.whatsapp.net"}
INTERNAL_SCHEMES = {"blob", "data", "about", "qrc", "file", "devtools", "chrome-error"}


def build_user_agent(profile: QWebEngineProfile, custom: str = "") -> str:
    """WhatsApp Web rejects user agents containing 'QtWebEngine'; present as plain Chrome."""
    if custom.strip():
        return custom.strip()
    return re.sub(r"\s*QtWebEngine/[\d.]+", "", profile.httpUserAgent())


def accept_language() -> str:
    """Follow the system locale so WhatsApp Web is shown in the user's own language."""
    name = QLocale.system().name().replace("_", "-")  # e.g. "id-ID"
    if not name or name == "C":
        name = "en-US"
    base = name.split("-")[0]
    parts = [name] + ([f"{base};q=0.9"] if base != name else [])
    if base != "en":
        parts.append("en;q=0.7")
    return ",".join(parts)


def make_profile(settings: Settings, parent: QObject) -> QWebEngineProfile:
    profile = QWebEngineProfile(APP_ID, parent)
    profile.setPersistentStoragePath(str(paths.DATA_DIR / "webengine"))
    profile.setCachePath(str(paths.CACHE_DIR / "webengine"))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
    profile.setHttpUserAgent(build_user_agent(profile, settings["user_agent"]))
    profile.setHttpAcceptLanguage(accept_language())
    return profile


def is_internal(url: QUrl) -> bool:
    return url.scheme() in INTERNAL_SCHEMES or url.host() in INTERNAL_HOSTS


class _LinkCatcher(QWebEnginePage):
    """Throw-away page for window.open(): its URL is handed to the system browser."""

    def __init__(self, profile: QWebEngineProfile, parent: QObject):
        super().__init__(profile, parent)
        QTimer.singleShot(15000, self.deleteLater)

    def acceptNavigationRequest(self, url, nav_type, is_main_frame) -> bool:
        if url.isEmpty() or url.scheme() == "about":
            return True
        QDesktopServices.openUrl(url)
        QTimer.singleShot(0, self.deleteLater)
        return False


class WaPage(QWebEnginePage):
    fullscreen_requested = Signal(bool)

    def __init__(self, profile: QWebEngineProfile, parent: QObject | None = None):
        super().__init__(profile, parent)
        self.permissionRequested.connect(self._on_permission)
        self.fullScreenRequested.connect(self._on_fullscreen)

        self._grant_types = {
            P.PermissionType.Notifications,
            P.PermissionType.MediaAudioCapture,
            P.PermissionType.MediaVideoCapture,
            P.PermissionType.MediaAudioVideoCapture,
            P.PermissionType.ClipboardReadWrite,
        }

    def grant_defaults(self) -> None:
        """WhatsApp sends no notifications until the permission is 'granted'. Grant it up front
        so the user does not have to click the in-page banner."""
        origin = QUrl("https://web.whatsapp.com")
        for perm_type in (P.PermissionType.Notifications,):
            perm = self.profile().queryPermission(origin, perm_type)
            if perm.state() != P.State.Granted:
                perm.grant()

    def _on_permission(self, permission) -> None:
        if permission.origin().host() in INTERNAL_HOSTS and \
                permission.permissionType() in self._grant_types:
            permission.grant()
        else:
            permission.deny()

    def _on_fullscreen(self, request) -> None:
        request.accept()
        self.fullscreen_requested.emit(request.toggleOn())

    def acceptNavigationRequest(self, url, nav_type, is_main_frame) -> bool:
        if is_main_frame and not is_internal(url):
            QDesktopServices.openUrl(url)
            return False
        return True

    def createWindow(self, _window_type):
        return _LinkCatcher(self.profile(), self)

    def javaScriptConsoleMessage(self, level, message, line, source) -> None:
        pass  # WhatsApp Web is very chatty on the console


class DownloadManager(QObject):
    """Saves downloads to the chosen folder and reports when they finish."""

    finished = Signal(str)  # file path
    failed = Signal(str)

    def __init__(self, profile: QWebEngineProfile, settings: Settings, parent_widget=None):
        super().__init__(profile)
        self._settings = settings
        self._parent_widget = parent_widget
        profile.downloadRequested.connect(self._on_download)

    @staticmethod
    def _unique(path: Path) -> Path:
        if not path.exists():
            return path
        n = 1
        while True:
            candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
            if not candidate.exists():
                return candidate
            n += 1

    def _on_download(self, item: QWebEngineDownloadRequest) -> None:
        name = item.downloadFileName() or "download"
        folder = self._settings.download_path
        folder.mkdir(parents=True, exist_ok=True)
        target = self._unique(folder / name)
        if self._settings["ask_download_location"]:
            chosen, _ = QFileDialog.getSaveFileName(self._parent_widget, "Save file", str(target))
            if not chosen:
                item.cancel()
                return
            target = Path(chosen)
        item.setDownloadDirectory(str(target.parent))
        item.setDownloadFileName(target.name)
        item.isFinishedChanged.connect(lambda: self._done(item, target))
        item.accept()

    def _done(self, item: QWebEngineDownloadRequest, target: Path) -> None:
        if item.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.finished.emit(str(target))
        elif item.state() != QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            self.failed.emit(target.name)
