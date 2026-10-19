"""PyInstaller entry point (the package itself is collected as a normal import)."""

import sys

from wadesk.app import main

sys.exit(main())
