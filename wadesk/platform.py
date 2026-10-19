"""Everything that differs between Linux, Windows and macOS, kept in one place.

Set WADESK_OS=linux|windows|macos to make the app behave as if it ran on that system
(used by the tests, which run on every OS).
"""

import getpass
import os
import re
import shutil
import sys
from pathlib import Path

from . import APP_ID, APP_NAME

LINUX, WINDOWS, MACOS = "linux", "windows", "macos"
OS_ENV = "WADESK_OS"
BUNDLE_ID = "io.github.pahrulirfan.wadesk"  # macOS bundle id, LaunchAgent label, Windows AppUserModelID


def current() -> str:
    forced = os.environ.get(OS_ENV, "").strip().lower()
    if forced in (LINUX, WINDOWS, MACOS):
        return forced
    if sys.platform.startswith("win"):
        return WINDOWS
    if sys.platform == "darwin":
        return MACOS
    return LINUX


def is_linux() -> bool:
    return current() == LINUX


def is_windows() -> bool:
    return current() == WINDOWS


def is_macos() -> bool:
    return current() == MACOS


def frozen() -> bool:
    """True when running from a PyInstaller build instead of from source."""
    return bool(getattr(sys, "frozen", False))


# ---------- file locations ----------
def app_dirs(env=None, home: Path | None = None) -> tuple[Path, Path, Path]:
    """(config, data, cache). Linux keeps the XDG locations so existing logins survive updates."""
    env = os.environ if env is None else env
    home = home or Path.home()
    system = current()
    if system == WINDOWS:
        roaming = Path(env.get("APPDATA") or home / "AppData" / "Roaming")
        local = Path(env.get("LOCALAPPDATA") or home / "AppData" / "Local")
        # Data and cache must not share a folder: both contain a "webengine" directory.
        return roaming / APP_NAME, local / APP_NAME, local / APP_NAME / "Cache"
    if system == MACOS:
        support = home / "Library" / "Application Support" / APP_NAME
        return support, support, home / "Library" / "Caches" / APP_NAME

    def xdg(var: str, fallback: str) -> Path:
        return Path(env.get(var) or home / fallback)
    return (xdg("XDG_CONFIG_HOME", ".config") / APP_ID, xdg("XDG_DATA_HOME", ".local/share") / APP_ID,
            xdg("XDG_CACHE_HOME", ".cache") / APP_ID)


# ---------- single instance and privileges ----------
def user_name() -> str:
    try:
        name = getpass.getuser()
    except (KeyError, OSError, ImportError):  # no passwd entry / no USERNAME variable
        name = ""
    return name or "user"


def socket_name() -> str:
    """Per-user name for the single-instance socket (a named pipe on Windows)."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", user_name())
    return f"{APP_ID}-{safe}"


def root_policy() -> str:
    """'ok', 'no-sandbox' (Linux: Chromium's sandbox cannot run as root) or 'refuse' (macOS)."""
    system = current()
    if system == WINDOWS or not hasattr(os, "geteuid") or os.geteuid() != 0:
        return "ok"
    return "refuse" if system == MACOS else "no-sandbox"


# ---------- how to start the app again (autostart) ----------
def launch_command() -> list[str]:
    exe = sys.executable
    system = current()
    if frozen():
        if system == LINUX:
            if os.environ.get("APPIMAGE"):
                return [os.environ["APPIMAGE"]]
            packaged = Path("/usr/bin") / APP_ID  # symlink created by the .deb
            if packaged.exists() and packaged.resolve() == Path(exe).resolve():
                return [str(packaged)]
        return [exe]
    if system == WINDOWS:
        pythonw = Path(exe).with_name("pythonw.exe")  # no console window at login
        return [str(pythonw if pythonw.exists() else exe), "-m", APP_ID]
    if system == LINUX:
        # Prefer the launcher created by install.sh: ~/.local/bin is often missing from PATH at login.
        installed = Path.home() / ".local" / "bin" / APP_ID
        if installed.exists():
            return [str(installed)]
        found = shutil.which(APP_ID)
        if found:
            return [found]
    return [exe, "-m", APP_ID]


# ---------- notifications ----------
def notifier_backend(which=None) -> tuple[str, str]:
    """('notify-send', path) on Linux when available, otherwise ('tray', '')."""
    if current() == LINUX:
        path = (which or shutil.which)("notify-send")
        if path:
            return "notify-send", path
    return "tray", ""


def restore_library_path(env=None) -> None:
    """PyInstaller points LD_LIBRARY_PATH at the bundled libraries. Programs we start (xdg-open, the
    browser, notify-send) must get the original value back; the bundled Qt finds its own libraries
    through RUNPATH, so the app itself does not need it."""
    env = os.environ if env is None else env
    if not (frozen() and current() == LINUX):
        return
    original = env.pop("LD_LIBRARY_PATH_ORIG", None)
    if original:
        env["LD_LIBRARY_PATH"] = original
    else:
        env.pop("LD_LIBRARY_PATH", None)


# ---------- user agent ----------
UA_PLATFORMS = {
    LINUX: "X11; Linux x86_64",
    WINDOWS: "Windows NT 10.0; Win64; x64",
    MACOS: "Macintosh; Intel Mac OS X 10_15_7",  # what Chrome reports on Apple silicon too
}


def user_agent(default: str) -> str:
    """A plain Chrome user agent for this OS, with the Chromium version of Qt WebEngine.

    WhatsApp Web rejects user agents that contain 'QtWebEngine/x.y'. Chrome itself only reports
    its major version ("Chrome/140.0.0.0"), so the result is indistinguishable from real Chrome.
    """
    m = re.search(r"Chrome/(\d+)", default)
    major = m.group(1) if m else "140"
    return (f"Mozilla/5.0 ({UA_PLATFORMS[current()]}) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{major}.0.0.0 Safari/537.36")


# ---------- wording ----------
def tray_place() -> str:
    """Where the tray icon lives, for user-facing text."""
    return "menu bar" if current() == MACOS else "system tray"


# ---------- start-up tweaks that need native calls ----------
def set_app_user_model_id() -> None:
    """Windows: group taskbar buttons and notifications under the app, not under python.exe."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(BUNDLE_ID)
    except (AttributeError, OSError):
        pass


def allow_foreground_handoff() -> None:
    """Windows: let the already running instance bring its window to the front."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.AllowSetForegroundWindow(-1)  # ASFW_ANY
    except (AttributeError, OSError):
        pass
