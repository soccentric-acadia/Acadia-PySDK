# Acadia-PySDK — specs

Remote: `git@github.com:SiliconCentric/Acadia-PySDK.git`
Stack: Python, uv-managed, src layout.

Consumes the `HalService` gRPC endpoint exposed by Acadia-Client — the same wire contract
Acadia-Server speaks.

## Layout

* `acadia-sdk/` — everything: source, tooling, docs, examples, the make workflow (setup / gen / check / build).
* `acadia-sdk/src/acadia_sdk/` — the package. Import name `acadia_sdk`, distribution name `acadia-sdk`.
* `acadia-sdk/src/acadia_sdk/_proto/` and `types/` — generated stubs, ~270 files, **committed on purpose**.
* `acadia_sdk` — deprecation shim re-exporting the public surface for callers on the old name. Lazy PEP 562 `__getattr__`, emits a `DeprecationWarning`, ships in the wheel.

## The regeneration exception

This is the one leaf that regenerates protos. Acadia-Client and Acadia-Server must not, because a
second copy of the generated C++ symbols causes ODR/duplicate-symbol link errors. That is a C++
constraint with no Python equivalent, so it does not apply here.
