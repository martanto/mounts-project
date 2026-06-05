"""Package-private constants.

Holds the MOUNTS base URLs and the default Indonesian volcano catalog used by
:meth:`mounts.core.MountsProject.extract` when no ``volcanoes`` argument is
provided.
"""

_MOUNTS_HOME_URL = "http://mounts-project.com"
_MOUNTS_TIMESERIES_URL = _MOUNTS_HOME_URL + "/timeseries"

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
