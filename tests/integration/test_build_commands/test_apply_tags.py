from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from konfusion_test_utils.konfusion_container import KonfusionContainer

    from konfusion.lib.imageref import ImageRef


def test_apply_tags(
    konfusion_container: KonfusionContainer, multiarch_image_in_zot_registry: ImageRef
) -> None:
    konfusion_container.run_cmd(
        [
            "konfusion",
            "--log-level",
            "DEBUG",
            "apply-tags",
            "--to-image",
            str(multiarch_image_in_zot_registry),
            "--tags",
            "test1",
            "test2",
        ]
    )

    def get_digest(tagged_image: ImageRef) -> str:
        proc = konfusion_container.run_cmd(
            ["skopeo", "inspect", "--format={{.Digest}}", f"docker://{tagged_image}"],
            capture_output=True,
        )
        return proc.stdout.strip()

    assert (
        get_digest(multiarch_image_in_zot_registry.replace(tag="test1", digest=None))
        == multiarch_image_in_zot_registry.digest
    )

    assert (
        get_digest(multiarch_image_in_zot_registry.replace(tag="test2", digest=None))
        == multiarch_image_in_zot_registry.digest
    )
