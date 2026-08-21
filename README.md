# Acadia-PySDK

## Project Description

Acadia-PySDK is the Python client leaf for the Acadia HAL service. Its package under
`acadia-sdk/` provides a Pythonic gRPC client for the `HalService` endpoint exposed by
Acadia-Client. The distribution package is `acadia-sdk`, imported as `acadia_sdk`; a deprecation
shim preserves the older public import surface. The package includes connection setup, device
discovery, one-shot execution, long-running execution, monitoring, event handling, typed
request/result round trips, and fake-server support for tests. Examples show connection,
long-running, and broad self-test workflows.

The package has API, quickstart, error-handling, versioning, and peripheral documentation. Its
test suite contains `test_connect.py`, `test_discovery.py`, `test_oneshot.py`,
`test_long_running.py`, `test_monitor.py`, `test_event.py`, and `test_types_roundtrip.py`, with
fixtures and `tests/fakes/fake_server.py` providing local infrastructure. These tests
demonstrate client-side behavior, not compatibility with a live board, protocol drift, or
server-side correctness.

The package Makefile and `acadia-sdk/pyproject.toml` define setup, generation, checking, and
build workflows. Run the configured pytest/check commands before changing public types or
generated protocol code. Authentication, TLS, endpoint configuration, streaming timing, and real
HAL results require manual validation.

The SDK is deliberately a leaf client: it should remain compatible with the protocol and
behavior published by Acadia-Client rather than duplicating HAL implementation. Fake-server
tests can validate serialization, callbacks, and lifecycle handling, but they cannot confirm
device timing, peripheral results, TLS deployment, or server backpressure. Those concerns need
an integration environment with the same generated contracts and endpoint configuration used by
operators.

## Feature Status

| # | Name / Description | Implemented? | Test Coverage? | Manual Test |
|---:|---|---|---|---|
| 1 | Installable package and import compatibility shim | Implemented | Package shim tests where present | [ ] Manual verification required |
| 2 | gRPC connection management | Implemented | `test_connect.py` | [ ] Manual verification required |
| 3 | Device discovery | Implemented | `test_discovery.py` | [ ] Manual verification required |
| 4 | One-shot execution | Implemented | `test_oneshot.py` | [ ] Manual verification required |
| 5 | Long-running execution | Implemented | `test_long_running.py` | [ ] Manual verification required |
| 6 | Monitoring and event handling | Implemented | `test_monitor.py`, `test_event.py` | [ ] Manual verification required |
| 7 | Typed request/result round trips | Implemented | `test_types_roundtrip.py` | [ ] Manual verification required |
| 8 | Fake server and pytest fixtures | Implemented | Used by package tests | [ ] Manual verification required |
| 9 | Examples and API documentation | Implemented | Execution unknown | [ ] Manual verification required |
| 10 | Protocol compatibility with Acadia-Client | Unknown | Generation/check exists; compatibility unverified | [ ] Manual verification required |

Python SDK leaf for the **Acadia** project (NVIDIA Jetson + STM32) in the SiliconCentric
`project-managers` fleet.

This leaf provides `acadia-sdk`, a Pythonic gRPC client for the `HalService` endpoint exposed by
`Acadia-Client`. The SDK distribution package is **`acadia-sdk`** (import name `acadia_sdk`); a
`acadia_sdk` deprecation shim re-exports the public surface for callers still on the old name.

The SDK source, tooling, docs, examples, and test suite live under [`acadia-sdk/`](acadia-sdk/).
See [`acadia-sdk/README.md`](acadia-sdk/README.md) for the full API, quickstart, and `make`
targets (`setup`, `gen`, `check`, `build`).

--- Part of the `Acadia` project in the `project-managers` fleet. See `docs/project-managers.md`
for the full 9-project / 8-leaf hierarchy and shared conventions.