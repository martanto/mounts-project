"""Cache reads must use UTF-8 encoding and a context-manager-closed handle."""

import json
import warnings

import pytest

from mounts.core import MountsProject
from mounts.utils import slugify


def test_cache_read_decodes_utf8(tmp_path) -> None:
    """A cache written with non-ASCII content must round-trip on read."""
    mp = MountsProject(output_dir=str(tmp_path))
    payload = {"data": [{"name": "Soufrière", "label": "°C"}]}

    cache_dir = tmp_path / "json"
    cache_dir.mkdir()
    slug = slugify("alpha-1")
    cache_file = cache_dir / f"{slug}.json"
    cache_file.write_text(json.dumps(payload), encoding="utf-8")

    assert mp._get_json("alpha", "1") == payload


def test_cache_read_closes_file_handle(tmp_path) -> None:
    """No ResourceWarning should leak from the cache-read path."""
    mp = MountsProject(output_dir=str(tmp_path))
    cache_dir = tmp_path / "json"
    cache_dir.mkdir()
    slug = slugify("alpha-1")
    (cache_dir / f"{slug}.json").write_text('{"data": []}', encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)
        result = mp._get_json("alpha", "1")

    assert result == {"data": []}
