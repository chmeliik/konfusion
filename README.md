# Konfusion

Konflux Fusion. CLI for implementing CI tasks. No confusion.

## Design

See [DESIGN.md](DESIGN.md).

## Development

Start by installing `make` and [`uv`][uv]. E.g.:

```bash
sudo dnf install make uv
```

### Virtual environment

Set up a virtual env, install `konfusion` and all the dependencies necessary
for development:

```bash
make .venv
source .venv/bin/activate
```

Play with `konfusion`:

```bash
konfusion --help
konfusion --version
konfusion apply-tags --tags v1 v1.0 --to-image quay.io/my-org/my-image:latest
```

### Static checks

* [pyright] for type-checking[^why-pyright]
  * _We may switch to [ty] when it's production-ready._
* [ruff] for linting and formatting

For the best development experience, integrate your editor with the pyright/pylance
and ruff LSP servers.

If you don't have these tools integrated with your editor, run them manually:

```bash
# check for issues and incorrect formatting
make check
# apply correct formatting
make format
# autofix some issues
make autofix
```

[^why-pyright]: You may be more familiar with [mypy] for type-checking Python code.
  But if you use something like VSCode, Vim or Emacs with a Python LSP server, there's
  a good chance you use pyright (in case of VSCode - [pylance], based on pyright).
  To better align with your editor experience, we use pyright for type-checking.

### Tests

We use [pytest] for all our tests, including [doctests][pytest-doctest].

To run tests locally, use:

```bash
make test
```

Or run `pytest` directly to make use of its full power:

```bash
source .venv/bin/activate
pytest --stepwise -vvv
```

### Integration tests

Pre-requisites:

* `podman`
* `openssl`

Run integration tests with:

```bash
make integration-test
```

Or directly using `pytest` (just copy the command from the Makefile).

#### `konfusion-test-utils`

Integration tests deploy an instance of the [Zot] container registry (a small, OCI-compliant
registry implementation). The tests also set up TLS for the registry by generating
a custom CA certificate and using it to sign Zot's server certificate.

This makes working with the registry a little tricky, which is why we have a separate
`konfusion-test-utils` package and CLI to make testing easier.

Run the registry for local testing:

```bash
source .venv/bin/activate
konfusion-test-utils run-zot-registry
# see the output for further instructions
```

Run commands in the `konfusion` container image in a way that makes interacting
with the registry straightworward:

```bash
konfusion-test-utils run-konfusion-container -- \
  skopeo copy docker://busybox:latest docker://localhost:5000/busybox:latest

konfusion-test-utils run-konfusion-container -- \
  konfusion apply-tags --to-image localhost:5000/busybox:latest --tags test
```

By default, `run-konfusion-container` will rebuild the Konfusion container image
every time. To use an existing image instead:

```bash
podman build -t localhost/konfusion:latest .
export TEST_KONFUSION_CONTAINER_IMAGE=localhost/konfusion:latest

konfusion-test-utils run-konfusion-container -- \
  skopeo copy docker://busybox:latest docker://localhost:5000/busybox:latest
```

[uv]: https://docs.astral.sh/uv/
[ty]: https://github.com/astral-sh/ty
[ruff]: https://docs.astral.sh/ruff/
[mypy]: https://mypy.readthedocs.io/en/stable/
[pylance]: https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance
[pyright]: https://microsoft.github.io/pyright/#/
[pytest]: https://docs.pytest.org/en/stable/
[pytest-doctest]: https://docs.pytest.org/en/stable/how-to/doctest.html
[Zot]: https://zotregistry.dev/
