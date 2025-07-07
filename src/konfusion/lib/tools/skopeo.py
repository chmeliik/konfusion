from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

from konfusion.lib.tools import CliTool

if TYPE_CHECKING:
    from konfusion.lib.imageref import ImageRef

log = logging.getLogger(__name__)


class Skopeo(CliTool):
    """Wrapper for calling skopeo in a subprocess."""

    @classmethod
    def find_in_path(cls) -> Self:
        """Find skopeo in PATH."""
        return super().find_by_name("skopeo")

    def copy(self, source: ImageRef, dest: ImageRef, *additional_args: str) -> None:
        """Run 'skopeo copy ...'."""
        self.run_with_logging(
            [
                "copy",
                *additional_args,
                f"docker://{self._adjust_image(source)}",
                f"docker://{dest}",
            ]
        )

    def inspect_format(self, image: ImageRef, format: str) -> str:
        """Run 'skopeo inspect --format ...'."""
        return self.run_with_logging(
            [
                "inspect",
                "--no-tags",
                "--format",
                format,
                f"docker://{self._adjust_image(image)}",
            ]
        ).stdout

    def _adjust_image(self, image: ImageRef) -> ImageRef:
        if image.digest:
            # skopeo doesn't support image refs with both tag and digest
            return image.replace(tag=None)
        else:
            log.warning(
                "Image ref doesn't include digest, this may be unreliable: %s", image
            )
            return image
