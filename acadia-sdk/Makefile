# acadia-sdk Makefile — common developer tasks.

PYTHON ?= python3
PIP    ?= pip
PKG    := acadia_sdk

.PHONY: help venv install dev-install gen build test lint typecheck clean publish

help:
	@echo "acadia-sdk targets:"
	@echo "  gen        regenerate proto + dataclass bindings from Acadia-HAL/protos"
	@echo "  build      build sdist + wheel"
	@echo "  test       run pytest with coverage"
	@echo "  lint       run ruff"
	@echo "  typecheck  run mypy --strict"
	@echo "  clean      remove build artefacts"
	@echo "  publish    upload wheel + sdist to PyPI (requires PYPI_TOKEN)"

dev-install:
	$(PIP) install -e .[dev]

gen:
	$(PYTHON) tools/gen_proto.py
	$(PYTHON) tools/gen_types.py

build:
	$(PYTHON) -m build

test:
	$(PYTHON) -m pytest --cov=$(PKG) --cov-report=term-missing

lint:
	$(PYTHON) -m ruff check src/$(PKG)

typecheck:
	$(PYTHON) -m mypy --strict src/$(PKG)

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

publish: build
	$(PYTHON) -m twine upload dist/*
