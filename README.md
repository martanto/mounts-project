# mounts-project

![Version](https://img.shields.io/badge/version-0.2.4-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active%20development-orange)
![PyPI](https://img.shields.io/pypi/v/mounts-project?label=pypi)
![Downloads](https://img.shields.io/pypi/dm/mounts-project?label=downloads)

Unofficial Python package
for [MOUNTS — Monitoring Unrest From Space](http://www.mounts-project.com).
Scrapes SO2 and thermal timeseries from the public MOUNTS pages and exposes them as pandas
DataFrames, ready to be written to CSV or XLSX.

<table align="center">
  <tr>
    <td align="center"><img src="https://raw.githubusercontent.com/martanto/mounts-project/main/assets/dashboard-1.jpg" alt="Dashboard overview" /></td>
    <td align="center"><img src="https://raw.githubusercontent.com/martanto/mounts-project/main/assets/dashboard-2.jpg" alt="Dashboard detail" /></td>
    <td align="center"><img src="https://raw.githubusercontent.com/martanto/mounts-project/main/assets/dashboard-3.jpg" alt="Thermal daily max calendar" /></td>
  </tr>
  <tr>
    <td align="center"><img src="https://raw.githubusercontent.com/martanto/mounts-project/main/assets/anomaly-overlay.jpg" alt="Anomaly overlay on SO2 vs Thermal" /></td>
    <td align="center"><img src="https://raw.githubusercontent.com/martanto/mounts-project/main/assets/image-gallery-1.jpg" alt="Anomaly overlay on SO2 vs Thermal" /></td>
    <td align="center"><img src="https://raw.githubusercontent.com/martanto/mounts-project/main/assets/image-gallery-2.jpg" alt="Anomaly overlay on SO2 vs Thermal" /></td>
  </tr>
</table>

## Disclaimer

This is an **unofficial** client and is not affiliated with the MOUNTS project. The information
presented within the MOUNTS website is provided "as is" and users bear all responsibility and
liability for their use of data and images, and for any indirect, incidental or consequential
damages arising out of any use of, or inability to use, the data.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Command-line interface](#command-line-interface)
- [Dashboard](#dashboard)
- [Quick Start](#quick-start)
- [About the project](#about-the-project)
- [Publications](#publications)
- [Credits & Acknowledgements](#credits--acknowledgements)
- [Use of the data](#use-of-the-data)
- [API Reference](#api-reference)
    - [`MountsProject`](#mountsprojectfilter_values01-output_dirnone-overwritefalse-verbosefalse)
    - [Image downloads](#image-downloads)
    - [Utility functions](#utility-functions)
    - [Logging helpers](#logging-helpers)

## Requirements

- **Python** `>=3.11`
- **uv** — Python package
  manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))

## Installation

Install from PyPI:

```bash
uv add mounts-project[dashboard]
```

Or with pip:

```bash
pip install mounts-project[dashboard]
```

Or install the latest from GitHub:

```bash
uv add git+https://github.com/martanto/mounts-project
```

Or, to work on the source:

```bash
git clone https://github.com/martanto/mounts-project
cd mounts-project
uv sync
```

## Command-line interface

Installing the package registers a `mounts` console script:

```bash
uv run mounts --help
uv run mounts save --help
```

### `mounts save`

Extract every volcano in the default catalog and write the result.

```bash
uv run mounts save --type csv                       # → ./output/csv/*.csv + all-volcanoes.csv
uv run mounts save --type xlsx --output-dir data    # → ./data/xlsx/*.xlsx + all-volcanoes.xlsx
uv run mounts save --overwrite -v                   # force re-fetch + verbose logs
uv run mounts save --extract-image --max-workers 16 # also download SO2/thermal images
```

| Option              | Default    | Description                                                              |
|---------------------|------------|--------------------------------------------------------------------------|
| `--type`            | `csv`      | Output format (`csv` or `xlsx`).                                         |
| `--output-dir`      | `./output` | Override the output directory.                                           |
| `--overwrite`       | off        | Re-fetch from MOUNTS even when cached JSON exists.                       |
| `--verbose`         | off        | Emit per-volcano info logs during extraction.                            |
| `--extract-image`   | off        | Also download SO2 and thermal images into `<output_dir>/images/`.        |
| `--max-workers`     | `8`        | Thread pool size for image downloads (only used with `--extract-image`). |

### `mounts dashboard`

Launch the Streamlit dashboard. Any extra arguments are forwarded to
`streamlit run`:

```bash
uv run mounts dashboard
uv run mounts dashboard --server.port 9000 --server.headless true
```

## Dashboard

`mounts dashboard` opens a Streamlit app that groups the extracted data by
volcano and by data type (SO2 / Thermal). Install the extras first:

```bash
uv sync --extra dashboard
uv run mounts dashboard
```

The dashboard reads `output/all-volcanoes.csv` from the current working
directory. If it does not exist yet, click **Refresh data** in the sidebar
or run `uv run mounts save --type csv` once to populate it.

The **Volcano detail** page also includes an image gallery (since `0.2.1`)
showing the SO2 and thermal snapshots previously fetched via
`save(extract_image=True)`. Images live under
`output/images/<slug>/{so2,thermal}/` and are matched to the active volcano,
data type, and date range from the existing selectors — no extra index file
is required. The gallery renders as a 10-column grid with a per-tab
**Per page** dropdown (50 / 100 / 200) and a page selector, both kept in a
narrow control group above the thumbnails.

## Quick Start

Minimal example (see [`main.py`](main.py)):

```python
from mounts_project import MountsProject


def main():
    mounts = MountsProject(verbose=True)

    # Scrape every volcano in the built-in catalog
    mounts.extract()

    # Access the per-volcano DataFrames
    data = mounts.data

    # Export to ./output/xlsx/<volcano>.xlsx + ./output/all-volcanoes.xlsx
    mounts.save(filetype="xlsx")


if __name__ == "__main__":
    main()
```

Run it:

```bash
uv run python main.py
```

The full pipeline is chainable:

```python
MountsProject(verbose=True).extract().save(filetype="csv")
```

Outputs land under `./output/`:

```
output/
├── all-volcanoes.csv
├── csv/
│   ├── lewotobi-laki-laki.csv
│   ├── marapi.csv
│   └── ...
└── json/                # cached raw scrape; reused on subsequent runs
    ├── lewotobi-laki-laki-264180.json
    └── ...
```

To monitor your own list of volcanoes instead of the built-in Indonesian catalog, pass them to
`extract()`:

```python
volcanoes = [
    {"name": "Etna", "code": "211060"},
    {"name": "Stromboli", "code": "211040"},
]
MountsProject().extract(volcanoes=volcanoes).save()
```

To also download the SO2 and thermal images served by MOUNTS, set `extract_image=True`
on `save()`. Images land under `<output_dir>/images/<slug>/{so2,thermal}/`, and a
`figures.json` index is written next to the JSON cache by `extract()`:

```python
MountsProject(verbose=True).extract().save(extract_image=True, max_workers=8)
```

## About the project

MOUNTS is a project conceptualized and led by Sébastien Valade since April 2017. Its aim is
to develop an operational monitoring system for volcanoes worldwide using satellite imagery.
It currently focuses on processing of Sentinel-1 (SAR), Sentinel-2 (SWIR), and Sentinel-5P (TROPOMI)
data.
Artificial intelligence "plugins" are developed and implemented in the processing chain to assist
monitoring tasks.

The project was from April 2017 to October 2019 funded by GEO.X and carried at TU-Berlin
(Computer Vision & Remote Sensing group, Prof. O. Hellwich) and GFZ
(Physics of Earthquakes and Volcanoes section, Priv. Doz. T. Walter).
Since March 2020, the project is carried at UNAM (Instituto de Geofísica, Mexico City).
The server running both the system and website is however still hosted at CV TU-Berlin,
with the kind agreement of Prof. Hellwich.

MOUNTS is strongly inspired by the operating MIROVA system,
with which tight collaborations are ongoing.

## Publications

### System description and recent eruptive events

- Valade, S., Ley, A., Massimetti, F., D'Hondt, O., Laiolo, M., Coppola, D., Loibl, D., Hellwich,
  O., Walter, T.R., Towards Global Volcano Monitoring Using Multisensor Sentinel Missions and
  Artificial Intelligence: The MOUNTS Monitoring System, *Remote Sens.*, 2019, 11, 1528

### Algorithm used to analyze Sentinel-2 images

- Massimetti, F., Coppola, D., Laiolo, M., Valade, S., Cigolini, C., Ripepe M., Volcanic Hot-Spot
  Detection Using SENTINEL-2: A Comparison with MODIS–MIROVA Thermal Data Series, *Remote Sens.*,
  2020, 12(5), 820

### Algorithm used to filter speckle from Sentinel-1 images

- Davis, T., Jain, V., Ley, A., D'Hondt, O., Valade, S., Hellwich, O., Reference-free despeckling of
  Synthetic-Aperture Radar images using a deep convolutional network, IGARSS 2020

### Algorithms developed to improve analysis of Sentinel-5P images

- Markus, B., Valade, S., Wöllhaf, M., Hellwich, O., Automatic retrieval of volcanic SO2 emission
  source from TROPOMI products, *Front. Earth Sci.*, 2023, 10

### Volcanological studies using data and analysis from MOUNTS (selection)

- Valade S., Coppola D., Campion R., Ley A., Boulesteix T., Taquet N., Legrand D., Laiolo M., Walter
  T. R. and De la Cruz-Reyna S. Lava dome cycles reveal rise and fall of magma column at
  Popocatépetl volcano, *Nature Communications*, 2023
- Coppola D., Valade S., Masias P., Laiolo M., Massimetti F., Campus A., Aguilar R., Anccasi R.,
  Apaza F., Ccallata B., Cigolini C., Cruz L. F., Finizola A., Gonzales K., Macedo O., Miranda R.,
  Ortega M., Paxi R., Taipe E., and Valdivia D. Shallow magma convection evidenced by excess
  degassing and thermal radiation during the dome-forming sabancaya eruption (2012–2020), *Bulletin
  of Volcanology*, 2022
- Burgi P.-Y., Valade, S., Coppola D., Boudoire G., Mavonga G., Rufino F., and Tedesco D.,
  Unconventional filling dynamics of a pit crater, *EPSL*, 2021

## Credits & Acknowledgements

### Funding sources

- 2017-2019: GEO.X 2-year postdoc fundings for the bottom-up project MOUNTS
- 2019: GEO.X Seed Funding 6-months postdoc for the project MOUNTS-AI dedicated to investigating
  Artificial Intelligence strategies for volcano monitoring.
- 2021-2023: PAPIIT project IA102221, 2-year project with part of the fundings dedicated to the
  purchase of new hardware for MOUNTS.

### TU-Berlin

- Andreas Ley developed and trained the convolutional neural network used by MOUNTS to detect ground
  deformation from Sentinel-1 interferograms.
- Olivier D'Hondt developed the NDSAR toolkit for SAR speckle filtering used in Valade et al. (
  2019).
- Timothy Davis & Vinit Jain, under the supervision of Andreas Ley & Sébastien Valade, developed and
  trained the convolutional neural network used by MOUNTS to despeckle Sentinel-1 SAR amplitude
  images: Davis et al. 2020 (IGARSS).
- Manuel Wöllhaf is contributing to the development of the new backend architecture of MOUNTS. He
  co-supervised Balazs Markus, whose research project focused on the automatic retrieval of volcanic
  SO2 emission source from TROPOMI products (Markus et al. 2023).
- MIROVA: members of MIROVA developed the algorithm used to detect hot pixels within the Sentinel-2
  SWIR bands (Massimetti et al., 2020). MIROVA is a collaborative project between the Universities
  of Turin and Firenze (Italy). Developments are underway to increase the interactivity between
  MOUNTS and MIROVA.
- LGS (University of Firenze): many thanks to friends and former colleagues of the Laboratorio di
  Geofisica Sperimentale (LGS), from whom much was learnt. This website is inspired by the unique
  interaction of research and monitoring that is achieved in this group.
- Sentinel data are freely available through ESA's Copernicus Open Access Hub, and are partially
  processed with the free SNAP toolboxes. Earthquake catalogs are provided by GEOFON (GFZ Potsdam)
  and USGS, and interrogated using the Pyrocko Toolbox.

## Use of the data

The products available on the MOUNTS website are value-added products created from freely available
Sentinel data provided by ESA. The products are released under the following conditions: permission
to freely copy, share and quote for non-commercial purposes, with attribution to MOUNTS and ESA as
the original source. If used for academic purposes, contacting Sébastien Valade (
valade@igeofisica.unam.mx) and citing the above-mentioned publication (Valade et al. 2019, *Remote
Sensing*) is kindly appreciated.

## API Reference

### `MountsProject(filter_values=0.1, output_dir=None, overwrite=False, verbose=False)`

Orchestrator that holds the scraped data and drives the
`extract() → save()` pipeline.

**Constructor parameters**

| Parameter       | Type            | Default        | Description                                                                                                                            |
|-----------------|-----------------|----------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `filter_values` | `float \| None` | `0.1`          | Lower bound applied to the `value` column after extraction. Rows with `value <= filter_values` are dropped. `None` disables filtering. |
| `output_dir`    | `str \| None`   | `<cwd>/output` | Root directory for cached JSON and exported CSV/XLSX files.                                                                            |
| `overwrite`     | `bool`          | `False`        | Force re-fetching from MOUNTS even when a cached JSON file exists.                                                                     |
| `verbose`       | `bool`          | `False`        | Emit per-volcano info logs during fetch.                                                                                               |

**Attributes**

| Attribute  | Type                          | Description                                                                                                    |
|------------|-------------------------------|----------------------------------------------------------------------------------------------------------------|
| `data`     | `dict[str, pandas.DataFrame]` | Per-volcano DataFrames keyed by volcano name. Populated by `extract()`.                                        |
| `catalogs` | `list[dict[str, Any]]`        | Per-volcano metadata: `name`, `code`, `updated_at`. Populated by `extract()`.                                  |
| `figures`  | `list[dict[str, Any]]`        | Per-volcano figure index: `name`, `code`, `index`, `so2`, `thermal` image URL lists. Populated by `extract()`. |
| `files`    | `list[str]`                   | Paths of files written by `save()`.                                                                            |

**Methods**

#### `extract(volcanoes=None) -> Self`

Fetch timeseries for a list of volcanoes and populate `self.data`, `self.catalogs`, and
`self.figures`. Also writes `<output_dir>/figures.json` (the figure index used by
`download_images_from_json`).

| Parameter   | Type                           | Default          | Description                                                                                                |
|-------------|--------------------------------|------------------|------------------------------------------------------------------------------------------------------------|
| `volcanoes` | `list[dict[str, str]] \| None` | built-in catalog | List of `{"name": ..., "code": ...}` entries. When `None`, uses the bundled 12-volcano Indonesian catalog. |

Returns `self` for chaining.

#### `extract_single_volcano(name, code) -> pandas.DataFrame`

Fetch and assemble the combined SO2 + thermal DataFrame for one volcano. Used internally by
`extract()`; call it directly if you want a single DataFrame without populating `self.data`.

| Parameter | Type  | Description                                                   |
|-----------|-------|---------------------------------------------------------------|
| `name`    | `str` | Volcano name (used for the `name` column and cache filename). |
| `code`    | `str` | MOUNTS volcano code (used in the URL and the `code` column).  |

Returns a DataFrame indexed by `datetime`, with columns `value`, `graph`, `type` (`"SO2"` or
`"Thermal"`), `date`, `time`, `code`, `name`.

#### `save(filetype="csv", extract_image=False, max_workers=8) -> Self`

Write per-volcano files plus a merged `all-volcanoes` export. Calls `extract()` automatically when
`self.data` is empty. When `extract_image=True`, also downloads the SO2 and thermal images
referenced by `self.figures` after the data files are written.

| Parameter       | Type                     | Default | Description                                                                            |
|-----------------|--------------------------|---------|----------------------------------------------------------------------------------------|
| `filetype`      | `Literal["csv", "xlsx"]` | `"csv"` | Output format.                                                                         |
| `extract_image` | `bool`                   | `False` | Also download SO2 and thermal images into `<output_dir>/images/<slug>/{so2,thermal}/`. |
| `max_workers`   | `int`                    | `8`     | Maximum concurrent download threads when `extract_image=True`.                         |

Writes:

- `<output_dir>/<filetype>/<slug>.<filetype>` per volcano
- `<output_dir>/all-volcanoes.<filetype>` (concatenated)

Returns `self` for chaining.

### Image downloads

From `mounts_project.download`. All downloaders run in parallel via a
`ThreadPoolExecutor` that shares a single `requests.Session` (pooled connections, reused
TLS handshakes). Individual URL failures are logged and skipped so a bad URL does not
abort the batch. URLs are resolved against the MOUNTS static asset host.

| Function                                                                                                  | Description                                                                                                             |
|-----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `download_image(image_url, output_dir=None, overwrite=False, verbose=False, session=None)`                | Download a single image. Skips re-downloading when the basename already exists unless `overwrite=True`.                 |
| `download_images(image_urls, output_dir=None, overwrite=False, verbose=False, max_workers=8)`             | Bulk download a flat list of image URLs into `output_dir` (defaults to `<cwd>/output/images`).                          |
| `download_images_from_dict(figures_dict, output_dir=None, overwrite=False, verbose=False, max_workers=8)` | For each `{"name", "so2", "thermal"}` entry, download both image lists into `<output_dir>/<slug(name)>/{so2,thermal}/`. |
| `download_images_from_json(figures_json, output_dir=None, overwrite=False, verbose=False, max_workers=8)` | Same as above, but reads the figure list from a JSON file (such as the `figures.json` written by `extract()`).          |

Standalone use, re-using the `figures.json` written by a previous `extract()` call:

```python
from mounts_project.download import download_images_from_json

download_images_from_json(
    "output/figures.json",
    output_dir="output/images",
    verbose=True,
)
```

### Utility functions

From `mounts_project.utils`:

| Function                             | Description                                                                                                                                             |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| `get_so2_values(graph_json)`         | Extract the SO2 timeseries from a MOUNTS Plotly graph payload (`data[2]`). Returns a DataFrame with `datetime`, `value`, `graph`, `type="SO2"`.         |
| `get_thermal_values(graph_json)`     | Extract the thermal timeseries from a MOUNTS Plotly graph payload (`data[0]`). Returns a DataFrame with `datetime`, `value`, `graph`, `type="Thermal"`. |
| `get_json_from_javascript(response)` | Regex-extract and parse the `var graph = {...}` JavaScript blob from a MOUNTS HTTP response. Raises `ValueError` if not found.                          |
| `slugify(text, hyphen="-")`          | Convert arbitrary text into a safe filename slug.                                                                                                       |
| `ensure_dir(path)`                   | Create a directory (and any missing parents) and return it as a `pathlib.Path`.                                                                         |

### Logging helpers

The package configures [loguru](https://loguru.readthedocs.io/) on import, writing a console stream
plus daily-rotated `logs/mounts_YYYY-MM-DD.log` and `logs/errors_YYYY-MM-DD.log` files in the
current working directory.

From `mounts_project.logger`:

| Function                     | Description                                                                               |
|------------------------------|-------------------------------------------------------------------------------------------|
| `get_logger()`               | Return the package-wide loguru `logger` instance.                                         |
| `set_log_level(level)`       | Change the console log level (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`). |
| `set_log_directory(log_dir)` | Change where log files are written.                                                       |
| `disable_logging()`          | Remove all handlers.                                                                      |
| `enable_logging()`           | Restore handlers after `disable_logging()`.                                               |

Set the environment variable `DISABLE_LOGGING=1` before import to skip handler setup entirely (
useful for subprocess workers).
