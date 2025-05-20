# ad_low_noise_float_2023

Links:
* https://github.com/petermaerki/ad_low_noise_float_2023_git
* Pico Firmware: https://github.com/petermaerki/ad_low_noise_float_2023_git/actions/workflows/software_pico_build_uf2.yaml
* python decoder: https://github.com/petermaerki/ad_low_noise_float_2023_git/actions/workflows/software_decoder_wheels.yml

## PC: Install decoder

Download artifact `cibw-wheels-windows-latest-1` from https://github.com/petermaerki/ad_low_noise_float_2023_git/actions/workflows/software_decoder_wheels.yml.

Unzip and move into `./wheels`.

```bash
# Command Prompt (Not powershell)
venv\Scripts\activate.bat
uv pip install --upgrade -r requirements.txt 
uv pip install wheels\ad_low_noise_float_2023_decoder-0.1.0-cp39-cp39-win_amd64.whl
```