"""In-process fake Acadia device, reusing the repo's test-suite fake server.

Lets the GUI run every example without real hardware: the toggle in the
toolbar starts ``tests/fakes/fake_server.py:FakeServer`` on an ephemeral
port and points the address field at it.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent


class FakeDevice:
    """Owns the optional in-process fake HAL server."""

    def __init__(self) -> None:
        self._server: Any | None = None
        self._address: str = ""

    @property
    def running(self) -> bool:
        return self._server is not None

    @property
    def address(self) -> str:
        return self._address

    def start(self) -> str:
        """Start the fake server; returns its ``host:port`` address."""
        if self._server is not None:
            return self._address
        server = self._load_fake_server()()
        self._address = str(server.start())
        self._server = server
        return self._address

    def stop(self) -> None:
        if self._server is not None:
            self._server.stop()
            self._server = None
            self._address = ""

    @staticmethod
    def _load_fake_server() -> type:
        root = str(_REPO_ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)
        try:
            from tests.fakes.fake_server import FakeServer
        except ImportError as exc:
            message = (
                "The built-in fake device needs the repository's test fixtures. "
                "Launch the GUI from the Acadia-PySDK repository root so that "
                "tests/fakes/fake_server.py is importable."
            )
            raise RuntimeError(message) from exc
        return FakeServer
