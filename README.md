# Acadia-PySDK

Python SDK leaf for the **Acadia** project (NVIDIA Jetson + STM32) in the
SiliconCentric `project-managers` fleet.

This leaf provides `acadia-sdk`, a Pythonic gRPC client for the `HalService`
endpoint exposed by `Acadia-Client`. The SDK distribution package is
**`acadia-sdk`** (import name `acadia_sdk`); a `acadia_sdk` deprecation shim
re-exports the public surface for callers still on the old name.

The SDK source, tooling, docs, examples, and test suite live under
[`acadia-sdk/`](acadia-sdk/). See [`acadia-sdk/README.md`](acadia-sdk/README.md)
for the full API, quickstart, and `make` targets (`setup`, `gen`, `check`,
`build`).

---
Part of the `Acadia` project in the `project-managers` fleet. See
`docs/project-managers.md` for the full 9-project / 8-leaf hierarchy and
shared conventions.