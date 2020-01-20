# pymeas2019

## Installation

- Picoscope Oscilloscope SW

- Picoscope Application - SDK: This is NOT required
- pip install -r requirements.txt
- Pymeas2019_noise
  - `git clone --recurse-submodules https://github.com/nanopysics/pymeas2019_noise.git`
- Start measurement
  - `cd pymeas2019_noise\measurement-actual`
  - `run_0_measure.bat`

## Directory structure

- `<TOPDIR>` The directory containing the file `TOPDIR.TXT`
  - `<TOPDIR>\measurement-actual` \
    The results of the actual measurement. \
    If the measurements are done, the directory may be moved away.

    - `run_0_measure.py` \
      This will run a measurement according the configuration within the file. \
      The results will be placed in a subfolder `raw-blue-2020-01-18_20-30-22`. \
      You may copy and rename this folder but you have to preserve `raw-<color>-<topic>`.

    - `run_1_plot.py` \
      This will loop over all `raw-xxx` directories and create `result_xxx` files.

    - `run_2_plot_composite.py` \
      You may still run this script when the folder is moved away. \
      This will loop over all `raw-xxx` directories and read `raw-xxx\result_summary.pickle`.
      Then the diagram `result_density.png` will be created.

## Workflow

### 0-Measure

Configure the measurement in `run_0_measure.py` and run it.
For every measurement, a new `raw-xx` folder will be created.

### 1-Condense

Condense the measured data in the `raw-xx` folders. This may be run without repeating the measurement.

### 2-Plot

This step will create a plot including all measurements available in the `raw-xx` folders.

