from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from konfusion.cli import CliCommand
from konfusion.lib.imageref import ImageRef

if TYPE_CHECKING:
    from argparse import ArgumentParser


@dataclass(frozen=True, kw_only=True)
class PushContainerfile(CliCommand):
    """Discover Containerfile from source code and attach it to container image."""

    source: Path
    context: Path
    file: Path | None
    for_image: ImageRef
    artifact_type: str
    tag_suffix: str

    @classmethod
    def setup_parser(cls, parser: ArgumentParser) -> None:
        super().setup_parser(parser)
        parser.add_argument("--source", type=Path, default=Path())
        parser.add_argument("--context", type=Path, default=Path())
        parser.add_argument("-f", "--file", type=Path)
        parser.add_argument("--for-image", required=True, type=ImageRef.parse)
        parser.add_argument(
            "--artifact-type", default="application/vnd.konflux.containerfile"
        )
        parser.add_argument("--tag-suffix", default=".containerfile")

    def run(self) -> None:
        for k, v in vars(self).items():
            print(f"{k}={v}")
