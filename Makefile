# Acadia-PySDK — top-level orchestration
#
# This Makefile wraps the acadia-sdk project with environment management
# and convenience targets. Most real work lives in acadia-sdk/Makefile;
# this layer takes care of creating the venv, installing the package
# in editable mode, and forwarding common targets.
#
# Usage:
#   make            # bootstrap venv + install + run lint/typecheck/test
#   make setup      # create venv and install acadia-sdk with dev extras
#   make gen        # regenerate proto + dataclass bindings
#   make test       # run pytest suite
#   make lint       # ruff
#   make typecheck  # mypy --strict
#   make check      # lint + typecheck + test
#   make build      # build wheel + sdist
#   make examples   # run example 01 against a fake server
#   make shell      # drop into a venv-activated subshell
#   make clean      # remove build artefacts
#   make distclean  # also remove the venv
#
# Override the Python interpreter:    make PYTHON=python3.12 setup

SHELL          := /bin/bash
.SHELLFLAGS    := -eu -o pipefail -c
.DEFAULT_GOAL  := all

PYTHON         ?= python3
VENV           ?= .venv
VENV_PY        := $(VENV)/bin/python
VENV_PIP       := $(VENV)/bin/pip
SDK_DIR        := acadia-sdk
ACTIVATE       := source $(VENV)/bin/activate
STAMP_DIR      := $(VENV)/.stamps
INSTALL_STAMP  := $(STAMP_DIR)/installed

# ANSI colours for friendlier output (auto-disabled when not a TTY).
ifneq (,$(findstring xterm,$(TERM)))
  C_BOLD := \033[1m
  C_DIM  := \033[2m
  C_OK   := \033[32m
  C_END  := \033[0m
else
  C_BOLD :=
  C_DIM  :=
  C_OK   :=
  C_END  :=
endif

define banner
	@printf "$(C_BOLD)==> %s$(C_END)\n" "$(1)"
endef

# ---------------------------------------------------------------------------
# Aggregate / help
# ---------------------------------------------------------------------------

.PHONY: all help check
all: check

help:
	@printf "$(C_BOLD)Acadia-PySDK$(C_END) — top-level targets\n\n"
	@awk 'BEGIN {FS=":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  $(C_OK)%-14s$(C_END) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\n$(C_DIM)Run \`make -C acadia-sdk help\` for the inner-project targets.$(C_END)\n"

check: lint typecheck test ## Run lint, typecheck, and the test suite

# ---------------------------------------------------------------------------
# Environment bootstrap
# ---------------------------------------------------------------------------

.PHONY: setup venv install reinstall
setup: $(INSTALL_STAMP) ## Create venv and install acadia-sdk[dev] in editable mode

venv: $(VENV_PY) ## Create the virtualenv only

$(VENV_PY):
	$(call banner,Creating virtualenv at $(VENV) using $(PYTHON))
	@$(PYTHON) -m venv $(VENV)
	@$(VENV_PIP) install --upgrade pip setuptools wheel >/dev/null

$(INSTALL_STAMP): $(VENV_PY) $(SDK_DIR)/pyproject.toml
	$(call banner,Installing acadia-sdk[dev] in editable mode)
	@$(VENV_PIP) install -e "$(SDK_DIR)[dev]"
	@mkdir -p $(STAMP_DIR)
	@touch $(INSTALL_STAMP)

install: $(INSTALL_STAMP) ## Alias for setup
reinstall: ## Force-reinstall the SDK into the existing venv
	@rm -f $(INSTALL_STAMP)
	@$(MAKE) install

# ---------------------------------------------------------------------------
# Forwarded targets (run inside the venv against acadia-sdk/)
# ---------------------------------------------------------------------------

.PHONY: gen build test lint typecheck cov publish
gen: $(INSTALL_STAMP) ## Regenerate proto + dataclass bindings
	$(call banner,Regenerating proto + dataclass bindings)
	@$(ACTIVATE) && $(MAKE) -C $(SDK_DIR) gen

build: $(INSTALL_STAMP) ## Build sdist + wheel
	$(call banner,Building distribution artefacts)
	@$(ACTIVATE) && $(VENV_PIP) install --quiet build && \
	  $(VENV_PY) -m build --outdir $(SDK_DIR)/dist $(SDK_DIR)

test: $(INSTALL_STAMP) ## Run pytest with coverage
	$(call banner,Running test suite)
	@$(ACTIVATE) && $(MAKE) -C $(SDK_DIR) test

lint: $(INSTALL_STAMP) ## Run ruff
	$(call banner,Linting with ruff)
	@$(ACTIVATE) && $(MAKE) -C $(SDK_DIR) lint

typecheck: $(INSTALL_STAMP) ## Run mypy --strict
	$(call banner,Type-checking with mypy --strict)
	@$(ACTIVATE) && $(MAKE) -C $(SDK_DIR) typecheck

cov: $(INSTALL_STAMP) ## Test with detailed coverage report
	@$(ACTIVATE) && cd $(SDK_DIR) && \
	  $(VENV_PY) -m pytest --cov=acadia_sdk --cov-report=term-missing --cov-report=html

publish: build ## Upload wheel + sdist to PyPI (requires twine + token)
	@$(ACTIVATE) && $(VENV_PIP) install --quiet twine && \
	  $(VENV_PY) -m twine upload $(SDK_DIR)/dist/*

# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

.PHONY: examples shell repl freeze
examples: $(INSTALL_STAMP) ## Smoke-run example 01 against a fake in-process server
	@$(ACTIVATE) && cd $(SDK_DIR) && $(VENV_PY) - <<'PY'
	import threading, time
	from tests.fakes.fake_server import FakeServer
	srv = FakeServer(); addr = srv.start()
	try:
	    import runpy, sys
	    sys.argv = ["01_connect_and_discover.py", addr]
	    runpy.run_path("examples/01_connect_and_discover.py", run_name="__main__")
	finally:
	    srv.stop()
	PY

shell: $(INSTALL_STAMP) ## Drop into a venv-activated subshell
	@$(ACTIVATE) && exec $${SHELL:-bash}

repl: $(INSTALL_STAMP) ## Open a Python REPL with acadia_sdk imported
	@$(ACTIVATE) && $(VENV_PY) -i -c "import acadia_sdk; print('acadia_sdk', acadia_sdk.__version__, 'ready as `acadia_sdk`')"

freeze: $(INSTALL_STAMP) ## Print pip freeze of the venv
	@$(VENV_PIP) freeze

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

.PHONY: clean distclean
clean: ## Remove build artefacts and caches (keeps the venv)
	$(call banner,Cleaning build artefacts)
	@rm -rf $(SDK_DIR)/build $(SDK_DIR)/dist $(SDK_DIR)/*.egg-info
	@rm -rf $(SDK_DIR)/.pytest_cache $(SDK_DIR)/.mypy_cache $(SDK_DIR)/.ruff_cache
	@rm -rf $(SDK_DIR)/htmlcov $(SDK_DIR)/.coverage
	@find $(SDK_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

distclean: clean ## Also nuke the virtualenv
	$(call banner,Removing virtualenv)
	@rm -rf $(VENV)
