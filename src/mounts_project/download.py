import os
import json
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from mounts_project.utils import slugify
from mounts_project.logger import logger
from mounts_project.constants import _MOUNTS_STATIC_URL

import requests


def download_images_from_dict(
    figures_dict: list[dict[str, Any]],
    output_dir: str | None = None,
    overwrite: bool = False,
    verbose: bool = False,
    max_workers: int = 8,
) -> None:
    """Download SO2 and thermal images for each figure entry in parallel.

    For every entry in ``figures_dict``, downloads the ``so2`` and ``thermal``
    image lists into ``<output_dir>/<slug(name)>/<kind>/``, where ``kind`` is
    ``"so2"`` or ``"thermal"``.

    Args:
        figures_dict (list[dict[str, Any]]): One entry per figure. Each entry
            must contain ``name`` (used to derive the output subdirectory via
            :func:`~mounts_project.utils.slugify`), ``so2`` (list of image URL
            paths), and ``thermal`` (list of image URL paths).
        output_dir (str | None, optional): Root directory under which the
            per-figure subdirectories are created. Defaults to ``None``.
        overwrite (bool, optional): Re-download even when a file with the same
            basename already exists. Defaults to ``False``.
        verbose (bool, optional): Emit info logs for cache hits and successful
            downloads. Defaults to ``False``.
        max_workers (int, optional): Maximum number of concurrent download
            threads per image batch. Defaults to ``8``.

    Raises:
        KeyError: If any entry in ``figures_dict`` is missing one of the
            required ``name``, ``so2``, or ``thermal`` keys.
    """
    for figure in figures_dict:
        name = figure["name"]
        image_dir = os.path.join(output_dir, slugify(name))

        for kind in ("so2", "thermal"):
            _image_dir = os.path.join(image_dir, kind)
            image_urls: list[str] = figure[kind]
            download_images(
                image_urls,
                _image_dir,
                overwrite=overwrite,
                verbose=verbose,
                max_workers=max_workers,
            )


def download_images_from_json(
    figures_json: str,
    output_dir: str | None = None,
    overwrite: bool = False,
    verbose: bool = False,
    max_workers: int = 8,
) -> None:
    """Download SO2 and thermal images from a JSON file of figure entries.

    Reads the JSON file at ``figures_json``, parses it, and forwards the
    decoded entries to :func:`download_images_from_dict`.

    Args:
        figures_json (str): Path to a JSON file containing a list of figure
            dicts. See :func:`download_images_from_dict` for the expected
            entry shape.
        output_dir (str | None, optional): Root directory under which the
            per-figure subdirectories are created. Defaults to ``None``.
        overwrite (bool, optional): Re-download even when a file with the same
            basename already exists. Defaults to ``False``.
        verbose (bool, optional): Emit info logs for cache hits and successful
            downloads. Defaults to ``False``.
        max_workers (int, optional): Maximum number of concurrent download
            threads per image batch. Defaults to ``8``.

    Raises:
        ValueError: If the decoded payload contains no entries.
    """
    with open(figures_json) as f:
        figures_dict: list[dict[str, Any]] = json.load(f)

    if len(figures_dict) == 0:
        raise ValueError(f"No data inside {figures_json}")

    download_images_from_dict(figures_dict, output_dir, overwrite, verbose, max_workers)


def download_images(
    image_urls: list[str],
    output_dir: str | None = None,
    overwrite: bool = False,
    verbose: bool = False,
    max_workers: int = 8,
) -> None:
    """Bulk download images from the MOUNTS static asset host in parallel.

    Fans the URLs out across a :class:`~concurrent.futures.ThreadPoolExecutor`
    that shares a single :class:`requests.Session`, so connections to the
    MOUNTS static host are pooled and TLS handshakes are reused. Failures on
    individual URLs are logged and swallowed so one bad URL does not abort the
    rest of the batch.

    Args:
        image_urls (list[str]): Paths of the images on the MOUNTS static host,
            each appended to :data:`_MOUNTS_STATIC_URL` to form a full URL.
        output_dir (str | None, optional): Directory to write the images into.
            Defaults to ``<cwd>/output/images``.
        overwrite (bool, optional): Re-download even when a file with the same
            basename already exists in ``output_dir``. Defaults to ``False``.
        verbose (bool, optional): Emit info logs for cache hits and successful
            downloads. Defaults to ``False``.
        max_workers (int, optional): Maximum number of concurrent download
            threads. Defaults to ``8``.
    """
    with (
        requests.Session() as session,
        ThreadPoolExecutor(max_workers=max_workers) as executor,
    ):
        futures = {
            executor.submit(
                download_image, url, output_dir, overwrite, verbose, session
            ): url
            for url in image_urls
        }
        for future in as_completed(futures):
            try:
                future.result()
            except requests.exceptions.RequestException:
                # Already logged inside download_image; keep the batch going.
                continue


def download_image(
    image_url: str,
    output_dir: str | None = None,
    overwrite: bool = False,
    verbose: bool = False,
    session: requests.Session | None = None,
) -> None:
    """Download an image from the MOUNTS static asset host.

    Resolves ``image_url`` against :data:`_MOUNTS_STATIC_URL`, writes the
    response body to ``<output_dir>/<basename>``, and skips the fetch when a
    file with the same basename already exists (unless ``overwrite`` is set).

    Args:
        image_url (str): Path of the image on the MOUNTS static host, appended
            to :data:`_MOUNTS_STATIC_URL` to form the full URL.
        output_dir (str | None, optional): Directory to write the image into.
            Defaults to ``<cwd>/output/images``.
        overwrite (bool, optional): Re-download even when a file with the same
            basename already exists in ``output_dir``. Defaults to ``False``.
        verbose (bool, optional): Emit info logs for cache hits and successful
            downloads. Defaults to ``False``.
        session (requests.Session | None, optional): Reusable HTTP session for
            connection pooling. When ``None``, a one-shot :func:`requests.get`
            call is used instead. Defaults to ``None``.

    Raises:
        requests.exceptions.RequestException: If the HTTP request to MOUNTS
            fails or returns a non-2xx status.
    """
    output_image_dir: str = (
        output_dir
        if output_dir is not None
        else os.path.join(os.getcwd(), "output", "images")
    )
    image_url = _MOUNTS_STATIC_URL + f"/{image_url}"

    os.makedirs(output_image_dir, exist_ok=True)
    image_filepath = os.path.join(output_image_dir, os.path.basename(image_url))

    if os.path.exists(image_filepath) and not overwrite:
        return

    try:
        response = (
            session.get(image_url, timeout=(5, 10))
            if session is not None
            else requests.get(image_url, timeout=(5, 10))
        )
        response.raise_for_status()

        with open(image_filepath, "wb") as f:
            f.write(response.content)

        if verbose:
            logger.info(f"Downloaded image: {image_filepath}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {image_url}: {e}")
        raise
