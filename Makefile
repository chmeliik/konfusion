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

.PHONY: requirements-build.txt
requirements-build.txt:
	uv run pybuild-deps compile -o requirements-build.txt

.PHONY: rpms.lock.yaml
rpms.lock.yaml:
	# rpm-lockfile-prototype depends on dnf bindings (the python3-dnf package on fedora)
	#   => need --system-site-packages
	uv venv --allow-existing --system-site-packages .rpm-lockfile-prototype-venv
	UV_PROJECT_ENVIRONMENT=.rpm-lockfile-prototype-venv uv run rpm-lockfile-prototype rpms.in.yaml
