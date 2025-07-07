PYTHON_VERSION = 3.12

default: .venv

.PHONY: .venv
.venv:
	uv sync --group dev --extra build-commands --python $(PYTHON_VERSION)

.PHONY: check
check: .venv
	uv run ruff check
	uv run ruff format --check --diff
	uv run pyright

.PHONY: format
format: .venv
	uv run ruff format

.PHONY: autofix
autofix: .venv
	uv run ruff check --fix

.PHONY: test
test: .venv
	pytest

.PHONY: requirements.txt
requirements.txt:
	uv export --frozen --all-packages --no-dev --no-emit-workspace -o requirements.txt
