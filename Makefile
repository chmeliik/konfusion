PYTHON_VERSION = 3.12

default: .venv

.PHONY: .venv
.venv:
	uv sync --group dev --extra build-commands --python $(PYTHON_VERSION)

.PHONY: check
check:
	uv run ruff check
	uv run ruff format --check --diff
	uv run pyright

.PHONY: format
format:
	uv run ruff format

.PHONY: autofix
autofix:
	uv run ruff check --fix

.PHONY: test
test:
	uv run pytest --ignore=tests/integration

.PHONY: integration-test
integration-test:
	uv run pytest tests/integration --log-cli-level DEBUG

.PHONY: requirements.txt
requirements.txt:
	uv export --frozen --all-packages --no-dev --no-emit-workspace -o requirements.txt
