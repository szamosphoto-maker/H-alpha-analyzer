# H-alpha Solar Analyzer

Standalone Windows GUI to count solar H-alpha filaments and active regions from a full-disk image.

## Use

1. Run `H-alpha-Solar-Analyzer.exe` (no separate Python installation required).
2. Select a H-alpha JPG, PNG, TIFF or TIF image with the Browse button.
3. Enter the observation location (default: Esztergom, Hungary).
4. Leave **Read date and time from filename** checked when the file name includes a full local timestamp; otherwise uncheck it and enter Date and Local time manually.
5. Click **Analyze**.

The program writes an annotated image and two CSV result files **next to the input image**. The original image remains unchanged.

**Timezone:** Europe/Budapest (CET/CEST); filename and manual timestamps are interpreted as local Hungarian time and converted to UTC automatically.

The image is neither rotated nor mirrored; B0 and P0 are computed solar ephemeris values, not a camera-orientation measurement. Prominences are not counted.

## Build executable on GitHub

Open **Actions → Build Windows EXE → Run workflow**. After a successful run, open the workflow run and download the artifact **H-alpha-Solar-Analyzer-Windows**. Unzip it to obtain `H-alpha-Solar-Analyzer.exe`.

## Run from Python

Use Python 3.11, then install dependencies:

```sh
python -m pip install -r requirements.txt
python halpha_gui.py
```

This is an experimental detector. Review labels on annotated images, especially for instruments/cameras other than the one used during development.
