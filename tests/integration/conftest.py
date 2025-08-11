from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from konfusion_test_utils.config import Config as UtilsConfig
from konfusion_test_utils.konfusion_container import KonfusionContainer
from konfusion_test_utils.zot import Zot, ZotIsDownError

from konfusion.lib.imageref import ImageRef

if TYPE_CHECKING:
    from collections.abc import Generator

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def config() -> UtilsConfig:
    return UtilsConfig.load_from_env()


@pytest.fixture(scope="session")
def zot_registry(config: UtilsConfig) -> Generator[Zot]:
    zot = Zot(config)
    try:
        zot.check_status()
        log.info("Using existing Zot instance at %s", zot.url)
        yield zot
    except ZotIsDownError:
        log.info("Starting new Zot instance")
        zot.run(restart=True, clean=config.clean_registry_storage)
        zot.wait_till_up()
        yield zot
        log.info("Stopping Zot instance")
        zot.kill()


@pytest.fixture(scope="session")
def konfusion_container(config: UtilsConfig) -> KonfusionContainer:
    repo_root = Path(__name__).parent.parent
    return KonfusionContainer.get(config, konfusion_rootdir=repo_root)


@pytest.fixture(scope="session")
def multiarch_image_in_zot_registry(
    zot_registry: Zot, konfusion_container: KonfusionContainer
) -> ImageRef:
    """Copy a multi-arch image to the local Zot registry and return its pullspec."""
    src_image = ImageRef.parse("registry.access.redhat.com/ubi9/ubi-micro:9.6")
    dest_image = ImageRef.parse(f"{zot_registry.host}/ubi9/ubi-micro:9.6")
    digest = "sha256:e62298fb53f7c510aa9c9e8b3cde34f5382648677339943d91609571453baaab"

    log.info("Copying %s to %s", src_image.replace(digest=digest), dest_image)
    proc = konfusion_container.run_cmd(
        [
            "skopeo",
            "copy",
            "--all",
            f"docker://{src_image.replace(tag=None, digest=digest)}",
            f"docker://{dest_image}",
        ],
        check=False,
        capture_output=True,
    )
    proc.check_returncode()

    return dest_image.replace(digest=digest)
