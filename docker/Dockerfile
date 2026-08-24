# syntax=docker/dockerfile:1
# ──────────────────────────────────────────────────────────────────────────────
# Acadia-PySDK — reproducible build + CI image.
#
# Installs uv (bundled in the base image), creates the venv, runs
# lint/typecheck/test, and builds the wheel + sdist into /dist.
# ──────────────────────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:0.7.0-bookworm-slim AS builder

WORKDIR /workspace

COPY pyproject.toml uv.lock* ./
# Create the venv and install deps first (cached even when sources change).
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra dev

# ── Test / lint / typecheck gate ─────────────────────────────────────────────
FROM builder AS check
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run ruff check src/acadia_sdk
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run mypy --strict --config-file pyproject.toml src/acadia_sdk
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run pytest tests -q

# ── Artifact stage (default) ─────────────────────────────────────────────────
FROM builder AS build
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run --with build python -m build --outdir /dist .

FROM scratch AS artifact
COPY --from=build /dist /dist
