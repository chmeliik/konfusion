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

[^why-pyright]: You may be more familiar with [mypy] for type-checking Python code.
  But if you use something like VSCode, Vim or Emacs with a Python LSP server, there's
  a good chance you use pyright (in case of VSCode - [pylance], based on pyright).
  To better align with your editor experience, we use pyright for type-checking.

[uv]: https://docs.astral.sh/uv/
[mypy]: https://mypy.readthedocs.io/en/stable/
[pylance]: https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance
[pyright]: https://microsoft.github.io/pyright/#/
