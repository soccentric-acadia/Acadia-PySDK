# Acadia Example Runner (GUI)

A PySide6 desktop app that executes every numbered example in
[`examples/`](../examples/) — one tab per example, streaming each script's
output live into its tab.

## Run

```bash
make gui          # installs PySide6 into the venv on first use, then launches
```

or manually:

```bash
uv pip install -e ".[gui]"
.venv/bin/python -m gui
```

## What you get

* **One tab per example** — tabs are auto-discovered from `examples/NN_*.py`,
  so new numbered examples appear as new tabs without any code change.
* **Toolbar** — device address (default `127.0.0.1:50051`), a built-in
  *fake device* toggle, **Run all**, and **Stop**.
* **Per tab** — the example's docstring, a Run button, a status line
  (queued / running / ✓ passed / ✗ failed / ■ stopped), and the live output log.
* **Run all** — executes the examples in numbered order, switching tabs as
  it goes. Runs on a worker thread, so the UI stays responsive.
* **Stop** — terminates the current script and skips the rest. The streaming
  examples (03–05) exit promptly.

## Notes

* The GUI runs the **actual example scripts** (as `python -u <script> <address>`
  subprocesses), so what you see is exactly what the scripts do — no duplicated
  example logic to keep in sync.
* The fake device reuses `tests/fakes/fake_server.py`; launch the GUI from the
  repository root so the test fixtures are importable. With the fake device
  running, every example executes against the in-process fake HAL and should
  pass.
* To run against a real Acadia device, stop the fake device and enter its
  address, e.g. `192.168.1.50:50051`.