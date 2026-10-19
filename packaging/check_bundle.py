#!/usr/bin/env python3
"""Fail if a PyInstaller build lacks part of the Qt WebEngine runtime.

    python packaging/check_bundle.py "dist/WA Desktop"
"""

import os
import sys
from pathlib import Path

REQUIRED = {
    "QtWebEngineProcess": lambda name, is_dir: name.startswith("QtWebEngineProcess"),
    "icudtl.dat": lambda name, is_dir: name == "icudtl.dat",
    "qtwebengine_resources.pak": lambda name, is_dir: name == "qtwebengine_resources.pak",
    "qtwebengine_locales/en-US.pak": lambda name, is_dir: name == "en-US.pak",
    "qtwebengine_locales": lambda name, is_dir: is_dir and name == "qtwebengine_locales",
    "wadesk/assets/icon.svg": lambda name, is_dir: name == "icon.svg",
}


def main(root: str) -> int:
    found = {key: None for key in REQUIRED}
    for folder, dirs, files in os.walk(root, followlinks=True):
        for name, is_dir in [(d, True) for d in dirs] + [(f, False) for f in files]:
            for key, match in REQUIRED.items():
                if found[key] is None and match(name, is_dir):
                    found[key] = Path(folder, name)
    for key, path in found.items():
        print(f"{'ok ' if path else 'MISSING'}  {key}" + (f"  ({path})" if path else ""))
    return 0 if all(found.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
