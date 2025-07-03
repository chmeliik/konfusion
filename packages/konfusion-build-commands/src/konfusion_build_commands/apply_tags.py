from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from konfusion.cli import CliCommand
from konfusion.lib.imageref import ImageRef

if TYPE_CHECKING:
    import argparse


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
    to_image: ImageRef

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser) -> None:
        super().setup_parser(parser)
        parser.add_argument("--tags", nargs="+", required=True)
        parser.add_argument("--to-image", required=True, type=ImageRef.parse)

    def run(self) -> None:
        print(f"applying tags {self.tags} to {self.to_image!r}")
