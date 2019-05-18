# pymeas2019

simple measure and documentation with python

## Workflow

### Step 0: measure

Output directory: `0_raw`

run: `pymeas2019\run_config_ch1.py`

This will measure `ch1` using the picoscope.

Note: Don't forget to remove obsolte results from 0_raw.
For example if you removed a frequency from the frequency-list, you must manually delete the obsolete data from directory `0_raw`.

### Step 1: condense data

Input directory: `0_raw`
Output directory: `1_condensed`

run: `pymeas2019\run_condense_0_to_1.py`

### Step 2: write result

Input directory: `1_condensed`
Output directory: `2_result`
