PYTHON_VERSION = 3.12

default: .venv

.PHONY: .venv
.venv:
	uv sync --group dev --python $(PYTHON_VERSION)

.PHONY: check
check: .venv
	.venv/bin/ruff check
	.venv/bin/ruff format --check --diff
	source .venv/bin/activate && pyright

.PHONY: format
format: .venv
	.venv/bin/ruff format

.PHONY: autofix
autofix: .venv
	.venv/bin/ruff check --fix
