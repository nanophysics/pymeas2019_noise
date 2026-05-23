# Install as a user

## Intro

### Required

* Windows 10/11
* Ubuntu 24.04 or newer
* No adminstrator rights are required.
* `ad_low_noise_float_2023` hardware

This document explains how to

* install uv (https://docs.astral.sh/uv/)
* run the `pymeas2019_noise` software (https://github.com/nanophysics/pymeas2019_noise)

### Remarks

* The python version installed is managed by `uv` and does NOT conflict with other python version installed via the python installer
* `uv` will handle in the background - no user interaction needed:
  * cloning of the git repo
  * installing python packages

### Updates

Whenever a program is starts, it will pick the NEWEST version available on https://github.com/nanophysics/pymeas2019_noise.

## Running on Windows

**Install uv - start powershell as user (not administrative) and run:**

```bash
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

**Create a directory `measurement_actual`:**

```bash
uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- pymeas2019 init
```

Open the windows explorer to enter the folder `measurement-actual` and double-click `run0_gui.bat` files.


## Running on Linux

**Install uv - start a terminal and run:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Create a directory `measurement_actual`:**

```bash
uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- pymeas2019 init
```

Enter folder `measurement-actual` and start `./run0_gui.sh`.

Now the gui opens.

If there is an error about "xvb", run: `sudo apt install xcb libxcb-cursor0 -y`.
