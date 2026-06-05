"""Unofficial Python client for the MOUNTS project.

Scrapes SO2 and thermal timeseries from http://www.mounts-project.com and
exposes them as pandas DataFrames. See :class:`mounts.core.MountsProject` for
the main entry point.
"""

from importlib.metadata import version

from mounts.core import MountsProject


__version__ = version("mounts")
__author__ = "Martanto"
__author_email__ = "martanto@live.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2026, Martanto"
__url__ = "https://github.com/martanto/mounts"

__all__ = [
    "__version__",
    "__author__",
    "__author_email__",
    "__license__",
    "__copyright__",
    "MountsProject",
]
