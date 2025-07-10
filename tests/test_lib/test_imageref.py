from __future__ import annotations

import pytest

from konfusion.lib.imageref import ImageRef


@pytest.mark.parametrize(
    ("imageref_str", "expect_result"),
    [
        (
            "registry.com/foo/bar",
            ImageRef(repo="registry.com/foo/bar", tag=None, digest=None),
        ),
        (
            "registry.com/foo/bar:baz",
            ImageRef(repo="registry.com/foo/bar", tag="baz", digest=None),
        ),
        (
            "registry.com/foo/bar@sha256:deadbeef",
            ImageRef(repo="registry.com/foo/bar", tag=None, digest="sha256:deadbeef"),
        ),
        (
            "registry.com/foo/bar:baz@sha256:deadbeef",
            ImageRef(repo="registry.com/foo/bar", tag="baz", digest="sha256:deadbeef"),
        ),
        (
            "registry.com:5000/foo/bar",
            ImageRef(repo="registry.com:5000/foo/bar", tag=None, digest=None),
        ),
        (
            "registry.com:5000/foo/bar:baz",
            ImageRef(repo="registry.com:5000/foo/bar", tag="baz", digest=None),
        ),
        (
            "registry.com:5000/foo/bar@sha256:deadbeef",
            ImageRef(
                repo="registry.com:5000/foo/bar", tag=None, digest="sha256:deadbeef"
            ),
        ),
        (
            "registry.com:5000/foo/bar:baz@sha256:deadbeef",
            ImageRef(
                repo="registry.com:5000/foo/bar", tag="baz", digest="sha256:deadbeef"
            ),
        ),
    ],
)
def test_imageref(imageref_str: str, expect_result: ImageRef) -> None:
    parsed = ImageRef.parse(imageref_str)
    assert parsed == expect_result
    assert str(parsed) == imageref_str
