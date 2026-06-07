"""Exercise the same call chain as `refresh_data()` in the dashboard.

Sets MOUNTS_OUTPUT_DIR to a temp folder, runs MountsProject on a 1-volcano
subset (so the test completes in seconds instead of minutes), and asserts
that CSV + image outputs land in that folder.
"""

import os
import sys
import shutil
from pathlib import Path


OUT = Path(__file__).parent / "refresh-smoke" / "output"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
os.environ["MOUNTS_OUTPUT_DIR"] = str(OUT)

from mounts_project import MountsProject  # noqa: E402
from mounts_project.constants import OUTPUT_DIR  # noqa: E402


print(f"MOUNTS_OUTPUT_DIR = {os.environ['MOUNTS_OUTPUT_DIR']}")
print(f"constants.OUTPUT_DIR = {OUTPUT_DIR}")
assert OUTPUT_DIR == str(OUT), "OUTPUT_DIR constant did not honour the env var"

ONE_VOLCANO = [{"name": "Anak Krakatau", "code": "262000"}]

MountsProject(overwrite=True, output_dir=OUTPUT_DIR).extract(
    volcanoes=ONE_VOLCANO
).save(filetype="csv", extract_image=True, max_workers=8)


csv_all = OUT / "all-volcanoes.csv"
csv_per = OUT / "csv" / "anak-krakatau.csv"
img_so2 = OUT / "images" / "anak-krakatau" / "so2"
img_th = OUT / "images" / "anak-krakatau" / "thermal"

problems = []
if not csv_all.exists():
    problems.append(f"MISSING: {csv_all}")
if not csv_per.exists():
    problems.append(f"MISSING: {csv_per}")
if not img_so2.is_dir() or not any(img_so2.iterdir()):
    problems.append(f"EMPTY:   {img_so2}")
if not img_th.is_dir() or not any(img_th.iterdir()):
    problems.append(f"EMPTY:   {img_th}")

print()
print("--- RESULT ---")
if problems:
    for p in problems:
        print(p)
    sys.exit(1)
else:
    so2_n = sum(1 for _ in img_so2.iterdir())
    th_n = sum(1 for _ in img_th.iterdir())
    print(f"all-volcanoes.csv: {csv_all.stat().st_size} bytes")
    print(f"per-volcano csv:   {csv_per.stat().st_size} bytes")
    print(f"so2 images:        {so2_n}")
    print(f"thermal images:    {th_n}")
    print("OK")
