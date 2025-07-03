from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from konfusion.cli import CliCommand
from konfusion.lib.imageref import ImageRef
from konfusion.lib.tools.skopeo import Skopeo

if TYPE_CHECKING:
    import argparse

log = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ApplyTags(CliCommand):
    """Apply tags to a container image in a registry.

    Takes additional tags from two sources:

    1) The --tags CLI argument: --tags v1 v1.0

    2) The 'konflux.additional-tags' label on the container image.
       The label is interpreted as a space-or-comma -separated list of tags.
       I.e., these all behave the same:

         LABEL konflux.additional-tags="v1 v1.0"
         LABEL konflux.additional-tags="v1,v1.0"
         LABEL konflux.additional-tags="v1, v1.0"
    """

    tags: list[str]
    image: ImageRef

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser) -> None:
        super().setup_parser(parser)
        parser.add_argument("--tags", nargs="+", required=True)
        parser.add_argument(
            "--to-image", dest="image", required=True, type=ImageRef.parse
        )

    def run(self) -> None:
        skopeo = Skopeo.find_in_path()

        def apply_tag(tag: str) -> None:
            dest_image = self.image.replace(tag=tag, digest=None)
            log.info("Tag %s -> %s", self.image, dest_image)
            skopeo.copy(self.image, dest_image, "--multi-arch=index-only")

        if self.tags:
            log.info("Applying tags from CLI argument")
            for tag in self.tags:
                apply_tag(tag)

        log.info("Inspecting %s to check for konflux.additional-tags label", self.image)

        additional_tags_label = skopeo.inspect_format(
            self.image, format='{{ index .Labels "konflux.additional-tags" }}'
        )
        additional_tags = self._parse_additional_tags_label(additional_tags_label)

        if additional_tags:
            log.info("Applying tags from konflux.additional_tags label")
            for tag in additional_tags:
                apply_tag(tag)
        else:
            log.info("konflux.additional-tags label not found or empty")

    @staticmethod
    def _parse_additional_tags_label(label: str) -> list[str]:
        """Parse the konflux.additional-tags label.

        >>> ApplyTags._parse_additional_tags_label("")
        []

        >>> ApplyTags._parse_additional_tags_label(" , ")
        []

        >>> ApplyTags._parse_additional_tags_label("v1")
        ['v1']

        >>> ApplyTags._parse_additional_tags_label("v1 v1.0")
        ['v1', 'v1.0']

        >>> ApplyTags._parse_additional_tags_label("v1,v1.0")
        ['v1', 'v1.0']

        >>> ApplyTags._parse_additional_tags_label(" v1, v1.0 ")
        ['v1', 'v1.0']
        """
        return list(filter(None, re.split(r"[\s,]+", label)))
