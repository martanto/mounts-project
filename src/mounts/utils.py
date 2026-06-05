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


def get_so2_values(graph_json: dict) -> pd.DataFrame:
    """Extract the SO2 timeseries from a MOUNTS graph payload.

    Reads the SO2 series from ``graph_json["data"][2]`` (a fixed position in the
    MOUNTS Plotly blob) and returns it as a DataFrame with ``datetime``,
    ``value``, ``graph``, and ``type`` columns.

    Args:
        graph_json (dict): Parsed MOUNTS Plotly ``graph`` object recovered from
            the embedded ``var graph = {...}`` JavaScript on the timeseries page.

    Returns:
        pd.DataFrame: DataFrame with columns ``datetime``, ``value``, ``graph``,
        and ``type`` (always ``"SO2"``).
    """
    so2_values = {
        "datetime": graph_json["data"][2]["x"],
        "value": graph_json["data"][2]["y"],
        "graph": graph_json["data"][2]["text"],
    }
    df = pd.DataFrame.from_dict(so2_values)
    df["type"] = "SO2"
    return df


def get_thermal_values(graph_json: dict) -> pd.DataFrame:
    """Extract the thermal timeseries from a MOUNTS graph payload.

    Reads the thermal series from ``graph_json["data"][0]`` (a fixed position in
    the MOUNTS Plotly blob) and returns it as a DataFrame with ``datetime``,
    ``value``, ``graph``, and ``type`` columns.

    Args:
        graph_json (dict): Parsed MOUNTS Plotly ``graph`` object recovered from
            the embedded ``var graph = {...}`` JavaScript on the timeseries page.

    Returns:
        pd.DataFrame: DataFrame with columns ``datetime``, ``value``, ``graph``,
        and ``type`` (always ``"Thermal"``).
    """
    thermal_values = {
        "datetime": graph_json["data"][0]["x"],
        "value": graph_json["data"][0]["y"],
        "graph": graph_json["data"][0]["text"],
    }
    df = pd.DataFrame.from_dict(thermal_values)
    df["type"] = "Thermal"
    return df


def get_json_from_javascript(response: requests.Response) -> dict:
    """Extract and parse the ``var graph = {...}`` blob from a MOUNTS response.

    MOUNTS has no public API; the timeseries page embeds its Plotly data as a
    JavaScript object literal. This function regex-locates that literal and
    parses it as JSON.

    Args:
        response (requests.Response): HTTP response from a MOUNTS
            ``/timeseries/<code>`` URL.

    Returns:
        dict: The parsed graph object containing Plotly traces under ``data``.

    Raises:
        ValueError: If the ``var graph = {...}`` assignment cannot be located in
            the response body.
    """
    var_graph = re.search(r"(?:^|\s|;)var\s+graph\s*=\s*([^']+})", response.text)

    if var_graph:
        string_graph = var_graph.group(1)
        json_graph = json.loads(string_graph)
        return json_graph

    raise ValueError(f"Could not extract graph from {response.text}")


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
