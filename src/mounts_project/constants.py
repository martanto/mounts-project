"""Package constants.

Holds the MOUNTS base URLs, the default Indonesian volcano catalog used by
:meth:`mounts_project.core.MountsProject.extract` when no ``volcanoes`` argument is
provided, and the path / unit / color constants consumed by the Streamlit
dashboard.
"""

import os


_MOUNTS_HOME_URL = "http://mounts-project.com"
_MOUNTS_TIMESERIES_URL = _MOUNTS_HOME_URL + "/timeseries"
_MOUNTS_STATIC_URL: str = _MOUNTS_HOME_URL + "/static"

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "all-volcanoes.csv")
XLSX_PATH = os.path.join(OUTPUT_DIR, "all-volcanoes.xlsx")

SO2_UNIT = "tons/day"
THERMAL_UNIT = "km²"

SO2_COLOR = "orange"
THERMAL_COLOR = "red"

ANOMALY_WINDOW_DEFAULT = 14
ANOMALY_SIGMA_DEFAULT = 2.0
RECENT_DAYS_DEFAULT = 30

_VOLCANOES: list[dict[str, str]] = [
    {
        "name": "Lewotobi Laki-laki",
        "code": "264180",
    },
    {
        "name": "Marapi",
        "code": "261140",
    },
    {
        "name": "Anak Krakatau",
        "code": "262000",
    },
    {
        "name": "Kerinci",
        "code": "261170",
    },
    {
        "name": "Karangetang",
        "code": "267020",
    },
    {
        "name": "Dukono",
        "code": "268010",
    },
    {
        "name": "Ili Lewotolok",
        "code": "264230",
    },
    {
        "name": "Ibu",
        "code": "268030",
    },
    {
        "name": "Semeru",
        "code": "263300",
    },
    {
        "name": "Raung",
        "code": "263340",
    },
    {
        "name": "Ijen",
        "code": "263350",
    },
    {
        "name": "Slamet",
        "code": "263180",
    },
]
