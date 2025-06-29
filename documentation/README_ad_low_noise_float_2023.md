# ad_low_noise_float_2023

Links:
* https://github.com/petermaerki/ad_low_noise_float_2023_git
* Pico Firmware: https://github.com/petermaerki/ad_low_noise_float_2023_git/actions/workflows/software_pico_build_uf2.yaml
* python decoder: https://github.com/petermaerki/ad_low_noise_float_2023_git/actions/workflows/software_decoder_wheels.yml


## Software installation

### The following steps in the windows "Powershell"

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  Installing to C:\Users\maerki\.local\bin
```

### As developer using git and venv

* git clone

```bash
git clone https://github.com/nanophysics/pymeas2019_noise.git
```

* install (windows: use "Cmd")

```bash
uv venv venv --python 3.13.5
venv\Scripts\activate
uv pip install --upgrade -e .
```

* Create batch files in folder `measurement_actual`

Run: VScode -> Run and Debug -> `ci_build_measurement_actual`
This will:
 * Create folder `artifacts`
 * Create batch files in `folder measurement_actual`

### As user (without using git)

```bash
uv venv venv --python 3.13.5
venv\Scripts\activate
uv pip install --upgrade -e .
```

```bash
uv run --python 3.13.5 --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python -m measurement_actual.run_0_gui
```

