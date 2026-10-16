"""Start the app automatically at login via ~/.config/autostart."""

import shutil
import sys
from pathlib import Path

from . import APP_NAME, paths


def _exec_command() -> str:
    # Prefer the launcher created by install.sh: ~/.local/bin is often missing from PATH at login.
    installed = Path.home() / ".local" / "bin" / "wadesk"
    if installed.exists():
        return str(installed)
    return shutil.which("wadesk") or f"{sys.executable} -m wadesk"


def set_enabled(enabled: bool) -> None:
    if not enabled:
        try:
            paths.AUTOSTART_FILE.unlink()
        except FileNotFoundError:
            pass
        return
    paths.AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.AUTOSTART_FILE.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        f"Exec={_exec_command()} --minimized\n"
        "Icon=wadesk\n"
        "X-GNOME-Autostart-enabled=true\n"
        "X-GNOME-Autostart-Delay=3\n",
        encoding="utf-8",
    )
