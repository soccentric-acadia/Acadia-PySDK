"""Background worker that executes example scripts as subprocesses.

PySide6 worker thread: the gRPC-heavy example scripts block, so they must
not run on the GUI thread. Output lines and lifecycle events travel back
to the window through queued signal connections.
"""
from __future__ import annotations

import contextlib
import subprocess
import sys
import threading

from PySide6.QtCore import QThread, Signal

from gui.examples import ExampleScript

_TERMINATE_GRACE_S = 3.0


class ExampleRunner(QThread):
    """Run example scripts sequentially, streaming their output.

    Signals carry the *tab index* of the example they refer to so the
    window can route lines and status updates without bookkeeping.

    ``stop()`` terminates the currently running script and skips any
    remaining ones; streaming examples (03, 04, 05) then exit promptly, and
    one-shot examples return as soon as the process dies.
    """

    line_ready = Signal(int, str)
    example_started = Signal(int)
    example_finished = Signal(int, int)  # tab index, process exit code
    all_finished = Signal()

    def __init__(
        self,
        *,
        scripts: list[ExampleScript],
        tab_indices: list[int],
        address: str,
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)
        self._scripts = scripts
        self._tab_indices = tab_indices
        self._address = address
        self._stop_requested = threading.Event()
        self._process: subprocess.Popen[str] | None = None

    def stop(self) -> None:
        """Ask the runner to stop; safe to call from any thread."""
        self._stop_requested.set()
        process = self._process
        if process is not None and process.poll() is None:
            process.terminate()

    def run(self) -> None:
        for script, tab_index in zip(self._scripts, self._tab_indices, strict=True):
            if self._stop_requested.is_set():
                break
            self.example_started.emit(tab_index)
            returncode = self._run_script(tab_index, script)
            self.example_finished.emit(tab_index, returncode)
        self.all_finished.emit()

    def _run_script(self, tab_index: int, script: ExampleScript) -> int:
        command = [sys.executable, "-u", str(script.path), self._address]
        try:
            process = subprocess.Popen(
                command,
                cwd=str(script.path.parent.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            self.line_ready.emit(
                tab_index, f"[gui] could not launch {script.path.name}: {exc}"
            )
            return 1
        self._process = process
        stream = process.stdout
        assert stream is not None
        try:
            while True:
                line = stream.readline()
                if not line:
                    break
                if self._stop_requested.is_set():
                    break
                self.line_ready.emit(tab_index, line.rstrip("\r\n"))
        finally:
            self._reap(process)
        returncode = process.returncode
        return returncode if returncode is not None else 0

    def _reap(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=_TERMINATE_GRACE_S)
            except subprocess.TimeoutExpired:
                process.kill()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=_TERMINATE_GRACE_S)
        if process.stdout is not None:
            process.stdout.close()
