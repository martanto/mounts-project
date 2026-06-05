"""CLI entry point for the mounts package.

Exposes two subcommands:

    mounts save --type csv      # extract + save the default catalog
    mounts dashboard            # launch the Streamlit dashboard

Registered via ``[project.scripts] mounts = "mounts.cli:cli"`` in
``pyproject.toml``.
"""

import sys
import subprocess
from typing import Literal, cast
from importlib.resources import files

from mounts import MountsProject

import click


@click.group()
@click.version_option(package_name="mounts")
def cli() -> None:
    """Command-line interface for the MOUNTS scraper and dashboard."""


@cli.command()
@click.option(
    "--type",
    "filetype",
    type=click.Choice(["csv", "xlsx"], case_sensitive=False),
    default="csv",
    show_default=True,
    help="Output file format.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default=None,
    help="Override output directory (default: ./output).",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Re-fetch from MOUNTS even when cached JSON exists.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Emit per-volcano info logs during extraction.",
)
def save(
    filetype: str,
    output_dir: str | None,
    overwrite: bool,
    verbose: bool,
) -> None:
    """Extract every volcano in the default catalog and save to CSV/XLSX."""
    MountsProject(
        output_dir=output_dir,
        overwrite=overwrite,
        verbose=verbose,
    ).extract().save(filetype=cast(Literal["csv", "xlsx"], filetype.lower()))


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("streamlit_args", nargs=-1, type=click.UNPROCESSED)
def dashboard(streamlit_args: tuple[str, ...]) -> None:
    """Launch the Streamlit dashboard.

    Extra arguments are forwarded to ``streamlit run``, e.g.

        mounts dashboard --server.port 9000
    """
    dashboard_path = files("mounts").joinpath("dashboard.py")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(dashboard_path),
        *streamlit_args,
    ]
    raise SystemExit(subprocess.call(cmd))
