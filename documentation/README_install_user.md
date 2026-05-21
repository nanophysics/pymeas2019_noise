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

The starting point is `measurement_actual_windows.zip` which may be downloaded [here](https://github.com/nanophysics/pymeas2019_noise/tree/main/artifacts).

* Extract `measurement_actual_windows.zip` into `measurement_actual`.
* Start `measurement_actual\run_9_install_uv.ps1` to install `uv` and `python`.

  Hint: In Windows Explorer *\<right-mouse-click\>* on `run_9_install_uv.ps1` and 'Run in PowerShell'.
  Expected output:
  ```powershell
    Downloading uv 0.7.16 (x86_64-pc-windows-msvc)
    Installing to C:\Users\maerki\.local\bin
    uv.exe
    uvx.exe
    uvw.exe
    everything's installed!
    Installed Python 3.13.5 in 6.89s
    + cpython-3.13.5-windows-x86_64-none

    Type any key to terminate...
  ```
* Start the software by *\<left-mouse-double-click\>* on `run_0_gui.bat`.

  Expected output:
  ```bash
  uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python -m pymeas2019_noise.run_0_gui
    Updated https://github.com/nanophysics/pymeas2019_noise.git (6c73db3a18bc882bf5394ea59e37d57e0e5252de)
      Built pymeas2019-noise @ git+https://github.com/nanophysics/pymeas2019_noise.git@6c73db3a18bc882bf5394ea59e37d57e0e5252de
  Installed 34 packages in 1.81s
  logging to C:\Projekte\ETH-Fir\pymeas2019_noise_uv_test\measurement_actual\logger_gui.txt
  ```

  Now the gui opens.


## Running on Linux

The starting point is `measurement_actual_linux.zip` which may be downloaded [here](https://github.com/nanophysics/pymeas2019_noise/tree/main/artifacts).

* Install `uv`. On ubuntu, uv may be installed via snap store.
* `unzip measurement_actual_linux.zip`. This will create a folder `measurement_actual`.
* `chmod a+x measurement_actual/*.sh`
* `cd measurement_actual`
* Start the gui: `./run_0_gui.sh`

  Expected output:
  ```bash
  ./run_0_gui.sh 
      Updated https://github.com/nanophysics/pymeas2019_noise.git (75a4021ae894640665ea33dc3cc830d753113b3b)
      Updated https://github.com/petermaerki/ad_low_noise_float_2023_git.git (c55e548d8698e4aee3b0e0d70d6bbedd799e464f)
        Built pymeas2019-noise @ git+https://github.com/nanophysics/pymeas2019_noise.git@75a4021ae894640665ea33dc3cc830d753113b3b
        Built ad-low-noise-float-2023 @ git+https://github.com/petermaerki/ad_low_noise_float_2023_git.git@c55e548d8698e4aee3b0e0d70d6bbedd799e464f
  Installed 39 packages in 128ms
  logging to /tmp/measurement_actual/logger_gui.txt
  ```

  Now the gui opens.

If there is an error about "xvb", run: `sudo apt install xcb libxcb-cursor0 -y`.
