# Installation for the developer

## Links

* https://github.com/petermaerki/ad_low_noise_float_2023_git
* Pico Firmware: https://github.com/petermaerki/ad_low_noise_float_2023_git/actions/workflows/software_pico_build_uf2.yaml
* python decoder: https://github.com/petermaerki/ad_low_noise_float_2023_git/actions/workflows/software_decoder_wheels.yml
* zip-files `build_measurement`: https://github.com/nanophysics/pymeas2019_noise/actions/workflows/deploy_build_measurement.yml

## Intro

This page will guide you to
* Install git
* Install uv + python
* Clone the git repo
* create a venv
* Start the scripts using the bat-files.
* Start the scripts using the VSCode debugger

This setup allows you to
* Debug the application
* Change the source file and restart the application to verify the change.
* Commit changes back to the git-repo.

## Installation

### git + clone repo

https://git-scm.com/download/win
install using defaults

`git clone https://github.com/nanophysics/pymeas2019_noise.git`

### uv + python

Run `run_9_install_uv.ps1` as described in [README_install_user.md](README_install_user.md).

### Create a venv

* install (windows: use "Cmd")

```bash
uv venv venv
venv\Scripts\activate
# Install project and dependencies
uv pip install --upgrade -e .
# Create .bat files in `measurement_actual`
python -m pymeas2019_noise.ci_build_measurement_actual
```

### Start the scripts using the bat-files

In Windows explorer in folder `pymeas2019_noise\measurement_actual` *\<left-mouse-double-click\>* `run_0_gui.bat`.

Now the gui opens.

### Start the scripts using the VSCode debugger

Open `pymeas2019_noise\project.code-workspace` with VSCode.

Run: VScode -> Run and Debug -> run_0_gui and click the green triangle to start.

Now the gui opens.

In this configuration, you can set breakpoints and debug.
