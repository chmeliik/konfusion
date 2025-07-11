from __future__ import annotations

import logging
import shlex
import subprocess
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    import os
    from collections.abc import Sequence
    from pathlib import Path

    from konfusion_test_utils.config import Config

log = logging.getLogger(__name__)


class KonfusionContainer:
    def __init__(self, image_name: str, config: Config) -> None:
        self._image_name = image_name
        self._config = config

    @property
    def image_name(self) -> str:
        return self._image_name

    @classmethod
    def get(cls, config: Config, konfusion_rootdir: Path) -> Self:
        if config.konfusion_container_image:
            log.info(
                "Using existing TEST_KONFUSION_CONTAINER_IMAGE=%s",
                config.konfusion_container_image,
            )
            self = cls(config.konfusion_container_image, config)
        else:
            log.info(
                "Building Konfusion container image (name=localhost/konfusion:test)"
            )
            self = cls.build_image(
                image_name="localhost/konfusion:test",
                konfusion_rootdir=konfusion_rootdir,
                config=config,
            )
            log.info(
                "To skip building the image, set TEST_KONFUSION_CONTAINER_IMAGE to an existing image"
            )
            log.info(
                "E.g. 'export TEST_KONFUSION_CONTAINER_IMAGE=localhost/konfusion:latest'"
            )
        return self

    @classmethod
    def build_image(
        cls,
        image_name: str,
        konfusion_rootdir: Path,
        config: Config,
    ) -> Self:
        subprocess.run(
            ["podman", "build", "--tag", image_name, konfusion_rootdir],
            check=True,
        )
        return cls(image_name, config)

    def run_cmd(
        self,
        cmd: Sequence[str | os.PathLike[str]],
        podman_args: Sequence[str | os.PathLike[str]] = (),
        check: bool = True,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        podman_cmd: list[str | os.PathLike[str]] = [
            "podman",
            "run",
            *podman_args,
            "--rm",
            # allow the container to talk to the Zot registry running on localhost
            "--network=host",
        ]

        if self._config.ca_cert_path.exists():
            # Note: this cert location is undocumented and probably doesn't work for all tools.
            # But it is what most Konflux Tekton Tasks use. So if doesn't work for our tests,
            #   it probably won't work for the tasks either.
            cert_path_in_container = "/etc/pki/tls/certs/ca-custom-bundle.crt"
            podman_cmd.append(
                f"--volume={self._config.ca_cert_path.resolve()}:{cert_path_in_container}"
            )

        podman_cmd.append(self.image_name)
        podman_cmd.extend(cmd)

        log.debug("%s", shlex.join(map(str, podman_cmd)))
        proc = subprocess.run(
            podman_cmd, check=check, capture_output=capture_output, text=True
        )

        if capture_output:
            if stdout := proc.stdout.rstrip("\n"):
                log.debug("stdout>\n%s", stdout)
            if stderr := proc.stderr.rstrip("\n"):
                log.error("stderr>\n%s", stderr)

        return proc
