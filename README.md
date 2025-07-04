# Konfusion

Konflux Fusion. CLI for implementing CI tasks. No confusion.

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

[uv]: https://docs.astral.sh/uv/
[ty]: https://github.com/astral-sh/ty
[ruff]: https://docs.astral.sh/ruff/
[mypy]: https://mypy.readthedocs.io/en/stable/
[pylance]: https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance
[pyright]: https://microsoft.github.io/pyright/#/
[pytest]: https://docs.pytest.org/en/stable/
[pytest-doctest]: https://docs.pytest.org/en/stable/how-to/doctest.html
