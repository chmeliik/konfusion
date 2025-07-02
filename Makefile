PYTHON_VERSION = 3.12

default: .venv

.PHONY: .venv
.venv:
	uv sync --group dev --python $(PYTHON_VERSION)

.PHONY: check
check: .venv
	source .venv/bin/activate && pyright
