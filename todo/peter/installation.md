## Installation

Tested on Windows 10, Windows 7 and with the versions shown below.

### python
we use:
https://www.python.org/downloads/release/python-372/
python 3.7.2 32 bit, install using defaults

### git
https://git-scm.com/download/win
install using defaults

### install pymeas2019_noise
start `cmd.exe`

```
python -m pip install --upgrade pip
cd C:\data\temp        (for example, choose yourself)
git clone --recurse-submodules https://github.com/nanophysics/pymeas2019_noise.git
cd pymeas2019_noise
pip install -r requirements.txt
```

restart pc

* file explorer: pymeas2019_noise/measurement_actual
* double click run_0_plot_interactive.bat`
click start