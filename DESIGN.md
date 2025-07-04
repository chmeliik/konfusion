# Design considerations

## Each subcommand in a separate file

In [build-definitions], each task *had* to be self-contained because of the nature
of Bash-in-YAML. In a way, that was kind of a nice feature. Let's try to keep that
the same to some extent.

### Simple CLI "framework" based on the stdlib argparse

See [`src/konfusion/cli.py`](src/konfusion/cli.py).

To make a subcommand, all we have to do is subclass `CliCommand` and implement
the `setup_parser()` and `run()` methods. This makes it easy to have self-contained
commands in separate files.

See [`packages/konfusion-build-commands/src/konfusion_build_commands/`](packages/konfusion-build-commands/src/konfusion_build_commands/)
for examples of (to-be-)implemented commands.

## Allow anyone to add their own subcommand

If other Konflux teams want to use the same approach to implement their Tasks,
we should make that as easy as possible. But we should avoid centralizing everything
in one repo.

### Loading subcommands from "plugins"

Konfusion doesn't come with any subcommands out of the box. Instead, it loads
subcommands from plugins. A Python package can export as many subcommands
for Konfusion as it wants by using [entry points][entrypoints].

Example from [`packages/konfusion-build-commands/pyproject.toml`](packages/konfusion-build-commands/pyproject.toml):

```toml
[project.entry-points."konfusion.commands"]
apply-tags = "konfusion_build_commands.apply_tags"
push-containerfile = "konfusion_build_commands.push_containerfile"
```

Each entry point references a module that implements exactly one subclass of
`CliCommand`. Konfusion discovers them automatically and loads them into the CLI.

## Provide a re-usable shared library

It should be clear why this is important, but to provide an example:

There are many ways to parse a tag from a container image reference, but few of them
are correct. We should make it trivial for all subcommands to do it correctly and
consistently.

### Shared `konfusion.lib`

By depending on `konfusion`, packages that provide subcommands can easily make use
of the shared library.

See [`packages/konfusion-build-commands/`](packages/konfusion-build-commands/),
which is a standalone package in this repo and depends on `konfusion`.

## Real-time subprocess output

Most of what the subcommands will be doing is calling other CLI tools. Some commands
may take a long time and print messages along the way. The user should have the option
to see them in real time. Even if the program needs to use the stdout/stderr later.

### `CliTool` from `konfusion.lib.tools`

See [`src/konfusion/lib/tools/_cli_tool.py`](src/konfusion/lib/tools/_cli_tool.py).
The `CliTool` class is how subcommands should interface with CLI tools. It does
a bit of dark magic to enable logging subprocess output in real time while also
collecting that output.

For added consistency and convenience, specific CLI tools can get their own subclasses,
like [`src/konfusion/lib/tools/skopeo.py`](src/konfusion/lib/tools/skopeo.py).

## Synergize well with Tekton

Tekton allows users to pass array parameters. The only way to pass those arrays
to a Task step is to pass them as the args to a command or script. Here's how
the [buildah task][buildah-task] does it, for example:

```yaml
    args:
      - --build-args
      - $(params.BUILD_ARGS[*])
      - --labels
      - $(params.LABELS[*])
      - --annotations
      - $(params.ANNOTATIONS[*])
```

This results in Tekton running something like this:

```bash
bash -c "$buildah_script" \
  --build-args foo=1 bar=2 \
  --labels spam=3 eggs=4 \
  --annotations ham=5 jam=6
```

Because `buildah` doesn't parse args like this natively, the script has to do ugly
parsing to prepare the arguments for consumption:

```bash
# Split `args` into two sets of arguments.
while [[ $# -gt 0 ]]; do
    case $1 in
        --build-args)
            shift
            while [[ $# -gt 0 && $1 != --* ]]; do build_args+=("$1"); shift; done
            ;;
        --labels)
            shift
            while [[ $# -gt 0 && $1 != --* ]]; do LABELS+=("--label" "$1"); shift; done
            ;;
        --annotations)
            shift
            while [[ $# -gt 0 && $1 != --* ]]; do ANNOTATIONS+=("--annotation" "$1"); shift; done
            ;;
        *)
            echo "unexpected argument: $1" >&2
            exit 2
            ;;
    esac
done
```

### `argparse` and `nargs=*`

With Python's argparse and its [`nargs`][nargs], we can parse this style of arguments
natively without any trouble.
See [`packages/konfusion-build-commands/src/konfusion_build_commands/apply_tags.py`](packages/konfusion-build-commands/src/konfusion_build_commands/apply_tags.py).

[build-definitions]: https://github.com/konflux-ci/build-definitions
[entrypoints]: https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
[buildah-task]: https://github.com/konflux-ci/build-definitions/tree/main/task/buildah
[nargs]: https://docs.python.org/3/library/argparse.html#nargs
