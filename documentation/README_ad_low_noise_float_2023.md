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

### The following steps in the windows "Cmd"

```bash
uv venv venv --python 3.13.3
venv\Scripts\activate
uv pip install --upgrade -r requirements.txt
```

## PC: Install decoder

Download artifact `cibw-wheels-windows-latest-1` from https://github.com/petermaerki/ad_low_noise_float_2023_git/actions/workflows/software_decoder_wheels.yml.

Unzip and move into `./wheels`.

```bash
# Command Prompt (Not powershell)
venv\Scripts\activate.bat
uv pip install wheels\ad_low_noise_float_2023_decoder-0.1.2-cp313-cp313-win_amd64.whl
```
