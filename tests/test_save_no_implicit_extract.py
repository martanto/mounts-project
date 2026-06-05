"""save() must not silently scrape the default catalog when data is empty."""

import pytest

from mounts.core import MountsProject


def test_save_raises_when_data_empty(tmp_path) -> None:
    """Empty self.data should raise instead of triggering an implicit extract()."""
    mp = MountsProject(output_dir=str(tmp_path))

    with pytest.raises(RuntimeError, match="extract"):
        mp.save()
