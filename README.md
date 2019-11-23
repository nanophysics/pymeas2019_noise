# 2019-11-23
# TODO: config_common.py, list_ConfigFrequency = 
#   This should be possible to overwrite in run_setup_noise_density.py


# pymeas2019

simple measure and documentation with python

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
