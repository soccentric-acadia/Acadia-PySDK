# Acadia-PySDK Build and Deployment

## Scope

Acadia-PySDK is the Python SDK package under `acadia-sdk/`. The root Makefile uses `uv` to
create a virtual environment, install the SDK in editable mode with development extras,
regenerate HAL protobuf/dataclass bindings, run pytest/Ruff/mypy, and build wheel and source
distributions.

## 1. Prerequisites

- Python compatible with `acadia-sdk/pyproject.toml`: Python 3.10 or newer.
- `uv` on PATH, or pass `UV=/path/to/uv`; network access is needed for dependency installation
unless the environment is already provisioned.
- Protobuf sources/generation inputs from the expected sibling Acadia-HAL layout for `make gen`
and `make gen-check`.

Development dependencies include grpcio-tools, mypy-protobuf, pytest/pytest-cov, mypy, Ruff,
PyYAML, and protobuf/grpc type stubs.

## 2. Setup

```sh
make help
make setup
```

This creates `.venv` and installs `acadia-sdk[dev]` in editable mode. `make venv` creates only
the environment. The package source is under `acadia-sdk/src/acadia_sdk`.

## 3. Build and compile

```sh
make gen
make gen-check
make gen-clean
make build
```

`gen` regenerates protobuf and dataclass bindings; `gen-check` fails when committed generated
stubs differ; `gen-clean` removes generated protobuf output and regenerates it. `build` installs
the Python `build` frontend into the uv environment and writes the wheel and sdist to
`acadia-sdk/dist/`.

## 4. Test and lint

```sh
make test
make lint
make typecheck
make check
make
```

`test` runs pytest with coverage and a missing-lines report. `lint` runs Ruff over SDK source;
`typecheck` runs mypy strict with the package's configuration. `check` combines all three and is
the default `make` behavior. Tests use the fake server/harness and do not prove interoperability
with a deployed Acadia-Client or real board.

## 5. Packaging and artifacts

The distributable artifacts are `acadia-sdk/dist/*.whl` and `acadia-sdk/dist/*.tar.gz`. The
package metadata and package-data rules include generated `.pyi` files. No publish or
cloud-release target exists; upload/signing must be performed by an external release process
after review.

## 6. Deployment, install, and run

There is no root install, service, Docker, or cloud deployment target. To consume a locally
built package in another environment, install the generated wheel with that environment's Python
package manager, for example:

```sh
python -m pip install acadia-sdk/dist/<wheel-file>
```

The SDK is a client library, not a daemon. Runtime verification requires an Acadia-HAL/Client
gRPC endpoint and its network/TLS/authentication configuration, which are external to this
repository.

## 7. Cleanup

```sh
make clean
make distclean
```

`clean` removes package build/dist/egg-info, test and type/lint caches, coverage output, and
Python bytecode. `distclean` also removes `.venv` and its install stamps.

## 8. Hardware, cloud, and manual verification caveats

No hardware or cloud service is started by the Makefile. Fake-server tests validate SDK
contracts only. Manually verify generated bindings against the current Acadia-HAL protos,
package installation in a clean Python environment, real gRPC connectivity, TLS/certificate
handling, timeout/error behavior, and compatibility with the deployed client before publishing
or deploying an SDK release.
