"""Stateless helpers for parsing MOUNTS payloads and handling filesystem paths.

Includes Plotly trace extractors (:func:`get_so2_values`,
:func:`get_thermal_values`), the JavaScript-blob parser
(:func:`get_json_from_javascript`), and filename/path utilities
(:func:`slugify`, :func:`ensure_dir`).
"""

import re
import json
from pathlib import Path

import pandas as pd
import requests


def _find_trace(graph_json: dict, needles: tuple[str, ...]) -> dict:
    """Return the first Plotly trace whose ``name`` matches any of ``needles``.

    Case-insensitive substring match against the trace's ``name`` field. Raises
    ``KeyError`` with a descriptive message if no trace matches — this is the
    signal that MOUNTS has changed its page layout (CLAUDE.md flags trace
    ordering as the first thing to break, so we trade silent miscategorisation
    for a loud failure).

    Args:
        graph_json (dict): Parsed MOUNTS Plotly ``graph`` object.
        needles (tuple[str, ...]): Substrings to look for in each trace's
            ``name`` (case-insensitive).

    Returns:
        dict: The matching Plotly trace.

    Raises:
        KeyError: If no trace in ``graph_json["data"]`` matches ``needles``.
    """
    for trace in graph_json.get("data", []):
        name = str(trace.get("name", "")).lower()
        if any(needle.lower() in name for needle in needles):
            return trace
    raise KeyError(
        f"No MOUNTS trace matching {needles!r}; available names: "
        f"{[t.get('name') for t in graph_json.get('data', [])]}"
    )


def _extract_trace(
    graph_json: dict, needles: tuple[str, ...], label: str
) -> pd.DataFrame:
    """Build a DataFrame from the trace matching ``needles`` and tag it with ``label``.

    Args:
        graph_json (dict): Parsed MOUNTS Plotly ``graph`` object.
        needles (tuple[str, ...]): Case-insensitive substrings searched
            against each trace's ``name`` field.
        label (str): Value written into the resulting DataFrame's ``type``
            column.

    Returns:
        pd.DataFrame: DataFrame with ``datetime``, ``value``, ``graph``, and
        ``type`` (= ``label``) columns.

    Raises:
        KeyError: If no trace matches ``needles``.
    """
    trace = _find_trace(graph_json, needles)
    df = pd.DataFrame.from_dict(
        {"datetime": trace["x"], "value": trace["y"], "graph": trace["text"]}
    )
    df["type"] = label
    return df


def get_so2_values(graph_json: dict) -> pd.DataFrame:
    """Extract the SO2 timeseries from a MOUNTS graph payload.

    Locates the trace whose ``name`` contains ``"SO2"`` (case-insensitive) and
    returns its ``x``/``y``/``text`` arrays as a DataFrame.

    Args:
        graph_json (dict): Parsed MOUNTS Plotly ``graph`` object recovered from
            the embedded ``var graph = {...}`` JavaScript on the timeseries page.

    Returns:
        pd.DataFrame: DataFrame with columns ``datetime``, ``value``, ``graph``,
        and ``type`` (always ``"SO2"``).

    Raises:
        KeyError: If no SO2 trace is present in ``graph_json``.
    """
    return _extract_trace(graph_json, ("so2",), "SO2")


def get_thermal_values(graph_json: dict) -> pd.DataFrame:
    """Extract the thermal timeseries from a MOUNTS graph payload.

    Locates the trace whose ``name`` contains ``"thermal"`` (case-insensitive)
    and returns its ``x``/``y``/``text`` arrays as a DataFrame.

    Args:
        graph_json (dict): Parsed MOUNTS Plotly ``graph`` object recovered from
            the embedded ``var graph = {...}`` JavaScript on the timeseries page.

    Returns:
        pd.DataFrame: DataFrame with columns ``datetime``, ``value``, ``graph``,
        and ``type`` (always ``"Thermal"``).

    Raises:
        KeyError: If no thermal trace is present in ``graph_json``.
    """
    return _extract_trace(graph_json, ("thermal",), "Thermal")


def get_json_from_javascript(response: requests.Response) -> dict:
    """Extract and parse the ``var graph = {...}`` blob from a MOUNTS response.

    MOUNTS has no public API; the timeseries page embeds its Plotly data as a
    JavaScript object literal. This function locates that literal by walking
    the body and matching braces while tracking JSON string boundaries (so
    apostrophes, escaped quotes, and ``}`` characters inside strings don't
    truncate or overshoot the match), then parses the slice as JSON.

    Args:
        response (requests.Response): HTTP response from a MOUNTS
            ``/timeseries/<code>`` URL.

    Returns:
        dict: The parsed graph object containing Plotly traces under ``data``.

    Raises:
        ValueError: If the ``var graph = {...}`` assignment cannot be located,
            or the object literal has unbalanced braces.
    """
    text = response.text
    match = re.compile(r"\bvar\s+graph\s*=\s*\{").search(text)
    if match is None:
        raise ValueError(
            "Could not locate 'var graph = {...}' assignment in MOUNTS response"
        )

    start = match.end() - 1
    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if in_string:
            if c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])

    raise ValueError("Unbalanced braces in 'var graph = {...}' assignment")


def slugify(text: str, hyphen: str = "-") -> str:
    """Convert arbitrary text into a safe filename slug.

    Lowercases the input, replaces whitespace and underscores with the chosen
    separator, strips non-alphanumeric characters (except the separator), and
    collapses consecutive separators into one.

    Args:
        text (str): Text to slugify.
        hyphen (str): Separator character to use. Defaults to ``"-"``.

    Returns:
        str: Slugified filename-safe string.

    Examples:
        >>> slugify("Hello World")
        'hello-world'
        >>> slugify("Hello World", hyphen="_")
        'hello_world'
        >>> slugify("  Multiple   Spaces  ")
        'multiple-spaces'
    """
    s = text.lower()
    s = re.sub(r"[\s_]+", hyphen, s)
    escaped = re.escape(hyphen)
    s = re.sub(rf"[^a-z0-9{escaped}]", "", s)
    s = re.sub(rf"{escaped}+", hyphen, s)
    return s.strip(hyphen)


def ensure_dir(path: str | Path) -> Path:
    """Create a directory (and any missing parents) if it does not already exist.

    Args:
        path (str | Path): Absolute or relative directory path to create.

    Returns:
        Path: The resolved :class:`pathlib.Path` of the created directory.

    Raises:
        PermissionError: If the process lacks write permission for the target
            location or one of its parent directories.
        NotADirectoryError: If a component of ``path`` already exists as a file
            rather than a directory.

    Examples:
        >>> import tempfile, os
        >>> tmp = tempfile.mkdtemp()
        >>> result = ensure_dir(os.path.join(tmp, "a", "b"))
        >>> result.is_dir()
        True
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
