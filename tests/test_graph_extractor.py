"""Tests for the brace-balanced var graph extractor in mounts.utils."""

import pytest

from mounts.utils import get_json_from_javascript


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


def test_extracts_payload_with_apostrophes_in_strings() -> None:
    """Apostrophes inside JSON strings must not truncate the match."""
    html = """
    <script>
    var graph = {"data": [{"name": "O'Higgins", "x": [1]}]};
    </script>
    """

    result = get_json_from_javascript(_FakeResponse(html))
    assert result == {"data": [{"name": "O'Higgins", "x": [1]}]}


def test_ignores_trailing_html_with_extra_braces() -> None:
    """A `}` outside the graph literal must not overshoot the match."""
    html = """
    <script>var graph = {"data": [1, 2, 3]};</script>
    <style>.foo { color: red; }</style>
    """

    assert get_json_from_javascript(_FakeResponse(html)) == {"data": [1, 2, 3]}


def test_handles_escaped_quotes_inside_strings() -> None:
    """A `\\"` inside a JSON string must not close the string early."""
    html = r'<script>var graph = {"label": "she said \"hi\""};</script>'

    assert get_json_from_javascript(_FakeResponse(html)) == {
        "label": 'she said "hi"'
    }


def test_no_match_raises_clean_valueerror() -> None:
    """When the assignment is missing, the error message must not embed the body."""
    html = "<html>no graph here</html>"

    with pytest.raises(ValueError, match="Could not locate"):
        get_json_from_javascript(_FakeResponse(html))
