## Proposal for directory structure

- `<TOPDIR>/config_x`
  - Every directory includes these scripts:
    - `run_setup_noise_density.py`
      Do a measurement.
    - `run_plot_updater.py`
      Have a live-preview of the running measurment.
    - `run_plot.py`
      Create a plot of all results.

- Now, the `result`-folder may be renamed. Many such results folders may exist aside.
- Somehow, every `result`-folder defines it visible attributes.
- Variant A:
  - Coded in directoryname `result-color-topic`
  - File `attributes.txt` in directory.
  - Attributes programmed in `run_plot.py`

## Vorgehen

- Run using simulator
- implement directories
- Try with picoscope

# pymeas2019

simple measure and documentation with python

## Installation

- Picoscope Oscilloscope SW

- Picoscope Application - SDK: This is NOT required
- pip install -r requirements.txt
- Pymeas2019_noise
  - `git clone --recurse-submodules https://github.com/nanopysics/pymeas2019_noise.git`
- Start measurement
  - `cd pymeas2019_noise`
  - `run_setup_noise_density.bat`

## Terms

- Config_Setup
  - How and what is connected to the instrument
  - Input ranges
  - Output amplitude
  - A title of the setup. For example
    - Calibration measurement for Picoscope
    - DUT Gain 1
    - DUT Gain 2
- Config_Frequency
  - Frequency
  - Measurement duration
  - Sampling frequency
- Config_Common (Config_Measurement): Definitions for all Setups.
  - frequency list
    - Defaults for Config_Setup
- Config: The combination of
  - frequency (from Config_Common)
  - Config_Setup
- Measurement: A measurement from
  - frequency (from Config_Common)
  - Config_Setup
- Measurement_Condensed: The condensed results from a Measurement
  - frequency
  - Config_Setup
  - A+B: Complex
  - A+B: min/max
  - A+B: overload
- Result_Setup: All Measurement_Condensed for one Setup
  - Complex for every frequency
- Result_Common:

## Workflow

### Step 0: measure

Output directory: `0_raw`

run: `pymeas2019\run_config_ch1.py`

This will measure `ch1` using the picoscope.

Note: Don't forget to remove obsolete results from 0_raw.
For example if you removed a frequency from the frequency-list, you must manually delete the obsolete data from directory `0_raw`.

### Step 1: condense data

Input directory: `0_raw`

Output directory: `1_condensed`

run: `pymeas2019\run_condense_0to1.py`

### Step 2: write result

Input directory: `1_condensed`

Output directory: `2_result`
