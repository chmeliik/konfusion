from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from konfusion_test_utils.config import Config
from konfusion_test_utils.konfusion_container import KonfusionContainer
from konfusion_test_utils.zot import Zot, ZotAlreadyRunningError

log = logging.getLogger(__name__)


def setup_logging() -> None:
    """Set up logging for konfusion_test_utils."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)-8s] %(message)s"))

    for module in ["konfusion_test_utils"]:
        logger = logging.getLogger(module)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)


def run_zot(args: argparse.Namespace) -> None:
    restart: bool = args.restart
    clean: bool = args.clean

    config = Config.load_from_env()
    zot = Zot(config)

    if config.clean_registry_storage and not clean:
        log.warning("Ignoring TEST_CLEAN_REGISTRY_STORAGE setting")
        log.warning(
            "If you'd like to clean the storage, use the --clean flag (together with --restart)"
        )

    try:
        zot.run(restart=restart, clean=clean)
    except ZotAlreadyRunningError:
        print(
            f"Zot container (name={config.zot_container_name}) is already running.",
            "If you'd like to restart it, use the --restart flag.",
            sep="\n",
            file=sys.stderr,
        )
        sys.exit(1)

    zot.write_containers_auth_json(config.containers_auth_json_path)

    ca_path = config.ca_cert_path
    print(
        f"Zot container running (name={config.zot_container_name})",
        "",
        f"All Zot-related data is at {config.zot_root_dir}",
        "The data will persist between restarts. To start fresh, remove the directory.",
        "",
        f"Access the web UI at {zot.url}",
        f"  Username: {config.zot_username}",
        f"  Password: {config.zot_password}",
        f"Note: you will need to ignore the security warning or import {ca_path} into your browser.",
        "",
        "To interact with the registry using skopeo, use e.g.:",
        "  skopeo copy \\",
        f"    --authfile {config.containers_auth_json_path} \\",
        f"    --dest-cert-dir {ca_path.parent} \\",
        f"    containers-storage:{config.zot_container_image} docker://{zot.host}/zot:test",
        "",
        "To communicate with the registry API directly, use e.g.:",
        f"  curl --fail --user {config.zot_username}:{config.zot_password} --cacert {ca_path} {zot.url}/v2/",
        sep="\n",
    )


def run_in_konfusion(args: argparse.Namespace) -> None:
    cmd: list[str] = args.cmd
    tty: bool = args.tty
    interactive: bool = args.interactive

    config = Config.load_from_env()
    konfusion = KonfusionContainer.get(config, konfusion_rootdir=Path.cwd())

    podman_args = []
    if tty:
        podman_args.append("--tty")
    if interactive:
        podman_args.append("--interactive")

    proc = konfusion.run_cmd(cmd, podman_args, check=False)
    sys.exit(proc.returncode)


def main() -> None:
    """Run the CLI."""
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(title="subcommands", required=True)

    run_zot_cmd = subcommands.add_parser(
        "run-zot-registry",
        help="run an OCI-compliant container registry in a podman container",
    )
    run_zot_cmd.add_argument("--restart", action="store_true")
    run_zot_cmd.add_argument("--clean", action="store_true")
    run_zot_cmd.set_defaults(fn=run_zot)

    run_konfusion_cmd = subcommands.add_parser(
        "run-konfusion-container",
        help="run a command in the konfusion container image",
    )
    run_konfusion_cmd.add_argument("cmd", nargs="*", default=[])
    run_konfusion_cmd.add_argument("-t", "--tty", action="store_true")
    run_konfusion_cmd.add_argument("-i", "--interactive", action="store_true")
    run_konfusion_cmd.set_defaults(fn=run_in_konfusion)

    setup_logging()
    args = parser.parse_args()
    args.fn(args)
