from __future__ import annotations

import dataclasses
import re
from typing import Self


@dataclasses.dataclass(frozen=True)
class ImageRef:
    """Represents a container image reference.

    registry.example.org:5000/foo/bar:v0.1.2@sha256:deadbeef
    |-------------------------------| |----| |-------------|
                 $repo                 $tag      $digest
    """

    repo: str
    tag: str | None
    digest: str | None

    def __str__(self) -> str:
        s = self.repo
        if self.tag:
            s += ":" + self.tag
        if self.digest:
            s += "@" + self.digest
        return s

    @classmethod
    def parse(cls, imageref: str) -> Self:
        """Parse a string as an ImageRef.

        >>> ImageRef.parse("registry.example.org/foo/bar")
        ImageRef(repo='registry.example.org/foo/bar', tag=None, digest=None)

        >>> ImageRef.parse("registry.example.org:5000/foo/bar:baz@sha256:deadbeef")
        ImageRef(repo='registry.example.org:5000/foo/bar', tag='baz', digest='sha256:deadbeef')
        """
        repo_and_maybe_tag, _, maybe_digest = imageref.partition("@")
        digest = maybe_digest or None

        if re.search(r":[^/]*$", repo_and_maybe_tag):
            repo, _, tag = repo_and_maybe_tag.rpartition(":")
        else:
            repo = repo_and_maybe_tag
            tag = None

        return cls(repo, tag, digest)

    def replace(self, **changes: str | None) -> Self:
        return dataclasses.replace(self, **changes)
