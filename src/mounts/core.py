"""Top-level orchestrator for the MOUNTS scrape-and-export pipeline.

Defines :class:`MountsProject`, whose intended call chain is
``MountsProject(...).extract().save(filetype=...)``. Network responses are
cached as JSON under ``<output_dir>/json/`` so subsequent runs work offline.
"""

import os
import json
from typing import Any, Self, Literal

from mounts.utils import (
    slugify,
    ensure_dir,
    get_so2_values,
    get_thermal_values,
    get_json_from_javascript,
)
from mounts.logger import logger
from mounts.constants import _VOLCANOES, _MOUNTS_TIMESERIES_URL

import pandas as pd
import requests


_REQUEST_TIMEOUT = 30


class MountsProject:
    """Orchestrator for scraping and exporting MOUNTS timeseries data.

    Holds runtime state (extracted DataFrames, per-volcano catalogs, written
    file paths) and exposes the standard pipeline ``MountsProject(...).extract()
    .save(filetype=...)``. Network responses are cached as JSON under
    ``<output_dir>/json/`` so subsequent runs work offline unless
    ``overwrite=True``.

    Attributes:
        filter_values (float | None): Inclusive lower-bound filter applied to
            ``value``. Rows with ``value < filter_values`` are dropped;
            ``filter_values=0`` keeps zero readings. ``None`` disables
            filtering.
        output_dir (str): Root directory for cached JSON and exported files.
        overwrite (bool): If ``True``, re-fetch from MOUNTS even when a cached
            JSON file exists.
        verbose (bool): If ``True``, emit per-volcano info logs during fetch.
        data (dict[str, pd.DataFrame]): Per-volcano extracted DataFrames keyed
            by ``slugify(f"{name}-{code}")`` (the same slug used for the cache
            and output filenames) so two volcanoes sharing a name but
            differing in code stay distinct. Populated by :meth:`extract`.
        catalogs (list[dict[str, Any]]): Per-volcano metadata (``name``,
            ``code``, ``updated_at``). Populated by :meth:`extract`.
        files (list[str]): Paths of files written by :meth:`save`.
    """

    def __init__(
        self,
        filter_values: float | None = 0.1,
        output_dir: str | None = None,
        overwrite: bool = False,
        verbose: bool = False,
    ):
        """Initialise a :class:`MountsProject` instance.

        Args:
            filter_values (float | None, optional): Inclusive lower bound
                applied to the ``value`` column after extraction. Pass ``None``
                to disable; pass ``0`` to keep zero readings. Defaults to
                ``0.1``.
            output_dir (str | None, optional): Root directory for cached JSON
                and exported CSV/XLSX files. Defaults to ``<cwd>/output``.
            overwrite (bool, optional): Force re-fetching from MOUNTS even when
                a cached JSON file exists. Defaults to ``False``.
            verbose (bool, optional): Emit per-volcano info logs during fetch.
                Defaults to ``False``.
        """
        output_dir = (
            output_dir
            if output_dir is not None
            else os.path.join(os.getcwd(), "output")
        )

        self.filter_values = filter_values
        self.output_dir = output_dir
        self.overwrite = overwrite
        self.verbose = verbose

        self.data: dict[str, pd.DataFrame] = {}
        self.catalogs: list[dict[str, Any]] = []
        self.files: list[str] = []

    def extract_single_volcano(
        self,
        name: str,
        code: str,
    ) -> pd.DataFrame:
        """Fetch and assemble the combined SO2 + thermal DataFrame for one volcano.

        Calls :meth:`_get_json` (which handles the disk cache), then merges the
        SO2 and thermal series, parses datetimes, adds ``date``/``time``/
        ``code``/``name`` columns, sets ``datetime`` as the index, and applies
        the ``filter_values`` lower bound when set.

        Args:
            name (str): Volcano name (used for the ``name`` column and cache
                filename).
            code (str): MOUNTS volcano code (used in the URL and the ``code``
                column).

        Returns:
            pd.DataFrame: Combined SO2 and thermal observations indexed by
            ``datetime``, with columns ``value``, ``graph``, ``type``, ``date``,
            ``time``, ``code``, and ``name``.
        """
        graph_json = self._get_json(name, code)

        so2 = get_so2_values(graph_json)
        thermal = get_thermal_values(graph_json)

        df = pd.concat([so2, thermal])

        df["datetime"] = pd.to_datetime(df["datetime"])
        df["date"] = df["datetime"].apply(lambda x: x.strftime("%Y-%m-%d"))
        df["time"] = df["datetime"].apply(lambda x: x.strftime("%H:%M:%S"))
        df["code"] = code
        df["name"] = name
        df = df.set_index("datetime")

        if self.filter_values is not None:
            df = df[df["value"] >= self.filter_values]

        return df

    def extract(self, volcanoes: list[dict[str, str]] | None = None) -> Self:
        """Extract timeseries for a list of volcanoes and populate ``self.data``.

        Iterates over the given volcanoes (or the built-in :data:`_VOLCANOES`
        catalog when ``None``) and calls :meth:`extract_single_volcano` for
        each. Also builds ``self.catalogs`` with the last observation timestamp
        per volcano.

        Args:
            volcanoes (list[dict[str, str]] | None, optional): Volcanoes to
                extract. Each entry must have ``name`` and ``code`` keys. When
                ``None``, the built-in 12-volcano Indonesian catalog is used.
                Defaults to ``None``.

        Returns:
            Self: This :class:`MountsProject` instance, to enable chaining with
            :meth:`save`.
        """
        volcanoes = volcanoes if volcanoes is not None else _VOLCANOES

        self.data = {}
        self.catalogs = []
        for volcano in volcanoes:
            try:
                df = self.extract_single_volcano(volcano["name"], volcano["code"])
            except Exception as e:
                logger.error(f"[{volcano['name']}] extract failed: {e}")
                continue
            key = slugify(f"{volcano['name']}-{volcano['code']}")
            self.data[key] = df
            self.catalogs.append(
                {
                    "name": volcano["name"],
                    "code": volcano["code"],
                    "updated_at": df.index.max(),
                }
            )

        return self

    def save(
        self, filetype: Literal["csv", "xlsx"] = "csv", merge: bool = True
    ) -> Self:
        """Write per-volcano files plus a merged ``all-volcanoes`` export.

        Writes each DataFrame in ``self.data`` to
        ``<output_dir>/<filetype>/<slug>.<filetype>`` and a concatenated file to
        ``<output_dir>/all-volcanoes.<filetype>``.

        Args:
            filetype (Literal["csv", "xlsx"], optional): Output format. Defaults
                to ``"csv"``.
            merge (bool, optional): Reserved for future use; currently the
                merged file is always written. Defaults to ``True``.

        Returns:
            Self: This :class:`MountsProject` instance, to enable chaining.

        Raises:
            RuntimeError: If ``self.data`` is empty. Call :meth:`extract`
                explicitly first — ``save`` will not silently re-scrape the
                default catalog (which used to overwrite the user's intended
                custom list).
        """
        if len(self.data) == 0:
            raise RuntimeError(
                "No data to save; call extract() first."
            )

        save_dir = "csv" if filetype == "csv" else "xlsx"
        save_dir = os.path.join(self.output_dir, save_dir)
        ensure_dir(save_dir)

        files: list[str] = []

        dfs = []
        for key, df in self.data.items():
            filepath = os.path.join(save_dir, f"{key}.{filetype}")

            if filetype == "csv":
                df.to_csv(filepath, index=True)
            else:
                df.to_excel(filepath, index=True)

            dfs.append(df)

            logger.info(f"[{key}] Saved to: {filepath}")
            files.append(filepath)

        df_concat = pd.concat(dfs, ignore_index=False)

        if filetype == "csv":
            df_concat.to_csv(
                os.path.join(self.output_dir, "all-volcanoes.csv"), index=True
            )
        else:
            df_concat.to_excel(
                os.path.join(self.output_dir, "all-volcanoes.xlsx"), index=True
            )

        self.files = files

        return self

    def _get_json(
        self,
        name: str,
        code: str,
    ):
        """Return the parsed MOUNTS graph JSON for one volcano (cached on disk).

        Acts as the network/cache boundary: when a cached file exists at
        ``<output_dir>/json/<slug>.json`` and ``self.overwrite`` is ``False``,
        it is read from disk. Otherwise the MOUNTS timeseries page is fetched,
        the embedded ``var graph = {...}`` blob is extracted via
        :func:`get_json_from_javascript`, and the result is written to the
        cache before being returned.

        Args:
            name (str): Volcano name (used to build the cache filename).
            code (str): MOUNTS volcano code (used to build the request URL).

        Returns:
            dict: Parsed MOUNTS graph object containing Plotly traces under
            ``data``.

        Raises:
            requests.exceptions.RequestException: If the HTTP request to MOUNTS
                fails, times out (after ``_REQUEST_TIMEOUT`` seconds), or returns
                a non-2xx status.
        """
        url = _MOUNTS_TIMESERIES_URL + "/" + str(code)

        try:
            json_dir = os.path.join(self.output_dir, "json")
            ensure_dir(json_dir)

            filename = slugify(f"{name}-{code}")
            json_filepath = os.path.join(json_dir, f"{filename}.json")

            if not self.overwrite and os.path.exists(json_filepath):
                if self.verbose:
                    logger.info(f"File {json_filepath} already exists, skipping")
                graph_json: dict = json.load(open(json_filepath))
                return graph_json

            if self.verbose:
                logger.info(f"Extracting {name} ... ")

            response = requests.get(url, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
            graph_json = get_json_from_javascript(response)

            tmp_filepath = json_filepath + ".tmp"
            with open(tmp_filepath, "w", encoding="utf-8") as write_file:
                json.dump(graph_json, write_file, indent=2)
            os.replace(tmp_filepath, json_filepath)

            return graph_json

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting {name}: {e}")
            raise e
