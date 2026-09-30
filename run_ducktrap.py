"""Entry point for the packaged build (PyInstaller)."""

import sys

from duck_trap.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
