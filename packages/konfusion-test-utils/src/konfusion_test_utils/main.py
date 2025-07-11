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

    config = Config.load_from_env()
    zot = Zot(config)

    try:
        zot.run(restart=restart)
    except ZotAlreadyRunningError:
        print(
            f"Zot container (name={config.zot_container_name}) is already running.",
            "If you'd like to restart it, use the --restart flag.",
            sep="\n",
            file=sys.stderr,
        )
        sys.exit(1)

    ca_path = config.ca_cert_path
    print(
        f"Zot container running (name={config.zot_container_name})",
        "",
        f"All Zot-related data is at {config.zot_root_dir}",
        "The data will persist between restarts. To start fresh, remove the directory.",
        "",
        f"Access the web UI at {zot.url}",
        f"Note: you will need to ignore the security warning or import {ca_path} into your browser.",
        "",
        "To interact with the registry using skopeo, use e.g.:",
        f"  skopeo copy --dest-cert-dir {ca_path.parent} containers-storage:{config.zot_container_image} docker://{zot.host}/zot:test",
        "",
        "To communicate with the registry API directly, use e.g.:",
        f"  curl --fail --cacert {ca_path} {zot.url}/v2/",
        sep="\n",
    )


def run_in_konfusion(args: argparse.Namespace) -> None:
    cmd: list[str] = args.cmd
    entrypoint: str | None = args.entrypoint

    config = Config.load_from_env()

    if config.konfusion_container_image:
        konfusion = KonfusionContainer(config.konfusion_container_image, config)
    else:
        konfusion = KonfusionContainer.build_image(
            image_name="localhost/konfusion:test",
            konfusion_rootdir=Path.cwd(),
            config=config,
        )
        log.info(
            "To skip building the image, set TEST_KONFUSION_CONTAINER_IMAGE to an existing image"
        )
        log.info(
            "E.g. 'export TEST_KONFUSION_CONTAINER_IMAGE=localhost/konfusion:latest'"
        )

    proc = konfusion.run_cmd(cmd, check=False, entrypoint=entrypoint)
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
    run_zot_cmd.set_defaults(fn=run_zot)

    run_konfusion_cmd = subcommands.add_parser(
        "run-konfusion-container",
        help="run a command in the konfusion container image",
    )
    run_konfusion_cmd.add_argument("cmd", nargs="*", default=[])
    run_konfusion_cmd.add_argument("--entrypoint")
    run_konfusion_cmd.set_defaults(fn=run_in_konfusion)

    setup_logging()
    args = parser.parse_args()
    args.fn(args)
