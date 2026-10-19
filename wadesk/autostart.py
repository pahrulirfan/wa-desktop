"""Start the app automatically at login.

Linux: ~/.config/autostart/wadesk.desktop · Windows: HKCU\\...\\Run · macOS: a LaunchAgent.
"""

import os
import plistlib
import subprocess
from pathlib import Path

from . import APP_ID, APP_NAME, platform

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def desktop_file() -> Path:
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return config / "autostart" / f"{APP_ID}.desktop"


def launch_agent_file() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{platform.BUNDLE_ID}.plist"


def command() -> list[str]:
    return [*platform.launch_command(), "--minimized"]


def set_enabled(enabled: bool) -> None:
    system = platform.current()
    if system == platform.WINDOWS:
        _set_registry(enabled)
    elif system == platform.MACOS:
        _write_or_remove(launch_agent_file(), _launch_agent() if enabled else None)
    else:
        _write_or_remove(desktop_file(), _desktop_entry() if enabled else None)


def _write_or_remove(path: Path, content: bytes | None) -> None:
    if content is None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _desktop_entry() -> bytes:
    # Desktop-entry Exec quoting: arguments with spaces are wrapped in double quotes.
    exec_line = " ".join(f'"{a}"' if " " in a else a for a in command())
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        f"Exec={exec_line}\n"
        f"Icon={APP_ID}\n"
        "X-GNOME-Autostart-enabled=true\n"
        "X-GNOME-Autostart-Delay=3\n"
    ).encode("utf-8")


def _launch_agent() -> bytes:
    return plistlib.dumps({
        "Label": platform.BUNDLE_ID,
        "ProgramArguments": command(),
        "RunAtLoad": True,
        "ProcessType": "Interactive",
        "LimitLoadToSessionType": "Aqua",
    })


def _set_registry(enabled: bool) -> None:
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, subprocess.list2cmdline(command()))
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
