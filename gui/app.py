"""Acadia example-runner main window (PySide6).

Layout: a toolbar (device address, built-in fake device, Run all, Stop)
above one tab per numbered example. Each tab shows the example's
description, a Run button, a status line, and the streamed output of the
example script.
"""
from __future__ import annotations

import sys

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.examples import ExampleScript, default_examples_dir, discover_examples
from gui.fake_device import FakeDevice
from gui.runner import ExampleRunner

DEFAULT_ADDRESS = "127.0.0.1:50051"

_STATUS_QUEUED = '<span style="color:#8a8a8a">queued…</span>'
_STATUS_RUNNING = '<span style="color:#b8860b">● running…</span>'
_STATUS_OK = '<span style="color:#1a7f37">✓ passed</span>'
_STATUS_STOPPED = '<span style="color:#b8860b">■ stopped</span>'
_STATUS_FAILED = '<span style="color:#cf222e">✗ failed (exit {rc})</span>'
_LOG_MAX_LINES = 5000


class ExampleTab(QWidget):
    """Log pane + controls for one example script."""

    def __init__(self, script: ExampleScript, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.script = script
        self.state = "idle"

        description = QLabel(script.description or script.title, self)
        description.setWordWrap(True)

        self.run_button = QPushButton("Run", self)
        self._status = QLabel("idle", self)

        controls = QHBoxLayout()
        controls.addWidget(self.run_button)
        controls.addWidget(self._status)
        controls.addStretch(1)

        self.log = QPlainTextEdit(self)
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(_LOG_MAX_LINES)
        self.log.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))

        layout = QVBoxLayout(self)
        layout.addWidget(description)
        layout.addLayout(controls)
        layout.addWidget(self.log, 1)

    def mark_queued(self) -> None:
        self.state = "queued"
        self._status.setText(_STATUS_QUEUED)

    def mark_running(self) -> None:
        self.state = "running"
        self._status.setText(_STATUS_RUNNING)

    def mark_result(self, returncode: int) -> None:
        self.state = "finished" if returncode == 0 else "failed"
        if returncode == 0:
            self._status.setText(_STATUS_OK)
        elif returncode < 0:
            self.state = "stopped"
            self._status.setText(_STATUS_STOPPED)
        else:
            self._status.setText(_STATUS_FAILED.format(rc=returncode))

    def mark_stopped(self) -> None:
        self.state = "stopped"
        self._status.setText(_STATUS_STOPPED)

    def append_line(self, line: str) -> None:
        self.log.appendPlainText(line)
        bar = self.log.verticalScrollBar()
        bar.setValue(bar.maximum())


class MainWindow(QMainWindow):
    """One tab per example script, executed as a subprocess on demand."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Acadia SDK — Example Runner")
        self.resize(960, 640)

        self._fake = FakeDevice()
        self._runner: ExampleRunner | None = None
        self._scripts = discover_examples()

        # -- toolbar row -----------------------------------------------------
        address_label = QLabel("Device address", self)
        self.address_edit = QLineEdit(DEFAULT_ADDRESS, self)
        self.fake_button = QPushButton("Start fake device", self)
        self.fake_button.clicked.connect(self._toggle_fake)
        self.run_all_button = QPushButton("Run all", self)
        self.run_all_button.clicked.connect(self._run_all)
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._stop)

        toolbar = QHBoxLayout()
        toolbar.addWidget(address_label)
        toolbar.addWidget(self.address_edit, 1)
        toolbar.addWidget(self.fake_button)
        toolbar.addWidget(self.run_all_button)
        toolbar.addWidget(self.stop_button)

        # -- one tab per example ---------------------------------------------
        self.tabs = QTabWidget(self)
        self._tabs: list[ExampleTab] = []
        for index, script in enumerate(self._scripts):
            tab = ExampleTab(script, self)
            tab.run_button.clicked.connect(
                lambda _checked=False, tab_index=index: self._run_one(tab_index)
            )
            self._tabs.append(tab)
            self.tabs.addTab(tab, script.tab_label)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.addLayout(toolbar)
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage(
            f"{len(self._scripts)} examples loaded — address {DEFAULT_ADDRESS}"
        )

    # -- actions -------------------------------------------------------------

    def _address(self) -> str:
        return self.address_edit.text().strip() or DEFAULT_ADDRESS

    def _run_one(self, index: int) -> None:
        self._start_runner([index])

    def _run_all(self) -> None:
        self._start_runner(list(range(len(self._scripts))))

    def _start_runner(self, indices: list[int]) -> None:
        if self._runner is not None:
            return
        for index in indices:
            tab = self._tabs[index]
            tab.log.clear()
            tab.mark_queued()
        self._runner = ExampleRunner(
            scripts=[self._scripts[index] for index in indices],
            tab_indices=indices,
            address=self._address(),
            parent=self,
        )
        self._runner.example_started.connect(self._on_example_started)
        self._runner.line_ready.connect(self._on_line)
        self._runner.example_finished.connect(self._on_example_finished)
        self._runner.all_finished.connect(self._on_all_finished)
        self._runner.finished.connect(self._on_runner_thread_finished)
        self._set_busy(True)
        self._runner.start()

    def _stop(self) -> None:
        if self._runner is not None:
            self._runner.stop()
            self.statusBar().showMessage("Stopping…")

    def _toggle_fake(self) -> None:
        if self._fake.running:
            self._fake.stop()
            self.fake_button.setText("Start fake device")
            self.statusBar().showMessage("Fake device stopped")
            return
        try:
            address = self._fake.start()
        except RuntimeError as exc:
            QMessageBox.warning(self, "Fake device unavailable", str(exc))
            return
        self.address_edit.setText(address)
        self.fake_button.setText("Stop fake device")
        self.statusBar().showMessage(f"Fake device running at {address}")

    # -- runner callbacks (GUI thread) ----------------------------------------

    def _on_example_started(self, index: int) -> None:
        self.tabs.setCurrentIndex(index)
        self._tabs[index].mark_running()
        self.statusBar().showMessage(f"Running: {self._scripts[index].title}")

    def _on_line(self, index: int, line: str) -> None:
        self._tabs[index].append_line(line)

    def _on_example_finished(self, index: int, returncode: int) -> None:
        self._tabs[index].mark_result(returncode)

    def _on_all_finished(self) -> None:
        for tab in self._tabs:
            if tab.state == "queued":
                tab.mark_stopped()
        self.statusBar().showMessage("Finished")

    def _on_runner_thread_finished(self) -> None:
        self._set_busy(False)
        if self._runner is not None:
            self._runner.deleteLater()
            self._runner = None

    # -- housekeeping ----------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        for tab in self._tabs:
            tab.run_button.setEnabled(not busy)
        self.run_all_button.setEnabled(not busy)
        self.address_edit.setEnabled(not busy)
        self.fake_button.setEnabled(not busy)
        self.stop_button.setEnabled(busy)

    def closeEvent(self, event) -> None:
        if self._runner is not None:
            self._runner.stop()
            self._runner.wait(5000)
            self._runner.deleteLater()
            self._runner = None
        self._fake.stop()
        super().closeEvent(event)


def main(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("acadia-example-runner")
    window = MainWindow()
    if not window._scripts:
        QMessageBox.warning(
            window,
            "No examples found",
            "No numbered example scripts found under "
            f"{default_examples_dir()}.",
        )
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover — manual launch convenience
    raise SystemExit(main())
