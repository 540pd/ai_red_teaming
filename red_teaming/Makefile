# AI Red-Teaming Asset — common commands.
# Override the interpreter if you use a venv:  make PYTHON=.venv/bin/python install
PYTHON ?= python
PIP    ?= $(PYTHON) -m pip

.PHONY: help install install-easy install-python install-sophisticated \
        mock smoke easy python sophisticated clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install:  ## Install shared core (redteam_core) — do this first
	$(PIP) install -e .

install-easy:  ## Install Setup 1 tools (garak via pip, promptfoo via npm)
	$(PIP) install garak
	npm install

install-python:  ## Install Setup 2 tools
	$(PIP) install deepteam giskard deepeval datasets

install-sophisticated:  ## Install Setup 3 tools
	$(PIP) install pyrit deepeval

mock:  ## Start the local mock endpoint (for testing without a real app)
	$(PYTHON) examples/mock_endpoint.py

smoke:  ## Verify the target seam works (run `make mock` in another shell first)
	$(PYTHON) examples/smoke_test.py

easy:  ## Run Setup 1 (Promptfoo + Garak)
	./setups/1_easy/run.sh

python:  ## Run Setup 2 (DeepTeam + Giskard + DeepEval)
	$(PYTHON) setups/2_python/run.py

sophisticated:  ## Run Setup 3 (PyRIT) — use MODE=single|multi
	$(PYTHON) setups/3_sophisticated/run.py --mode $(or $(MODE),single)

clean:  ## Remove reports, caches, and build artifacts
	rm -rf reports/*/ .promptfoo garak_runs *.egg-info
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
