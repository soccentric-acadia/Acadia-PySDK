"""Entry point for the Acadia example-runner GUI.

Launch from the repository root::

    python -m gui          # or: make gui
"""
from __future__ import annotations

import sys


def _fail_no_pyside() -> None:
    sys.stderr.write(
        "PySide6 is not installed. Install it into the project venv with:\n"
        '  uv pip install -e ".[gui]"\n'
        "  (or simply: make gui)\n"
    )
    raise SystemExit(1)


try:
    from PySide6.QtCore import QCoreApplication  # noqa: F401 — probe only
except ImportError:
    _fail_no_pyside()


def run() -> int:
    from gui.app import main

    return main()


if __name__ == "__main__":
    raise SystemExit(run())
