# Software Design

## Class diagrams

### Build class diagrams

Run  `pip install --upgrade graphviz`

Run `documentation_design_build.sh`

This will create the files
- `documentation_design\classes_pymeas2019_noise.dot`
- `documentation_design\packages_pymeas2019_noise.dot`

### View class diagrams

- In VSCode install `joaompinto.vscode-graphviz`
- Open a `.dot` file an type
  - `ctrl+shift+v` - Toggle Preview
  - `ctrl+k` - Open Preview to the Side

## Source code formatting

- We try to use PEP8
- Code is formatted using `black`

Configuration is stored here

- .vscode/launch.json
- .vscode/settings.json
- .pylintrc
- .blackconfig.yaml

Run  `pip install --upgrade pip pylint black`

To format a file, right-click and select `Format Document` in the source code.

Before commit, run the `Lint` launch-target in VSCode.
Before commit, run the `Black` launch-target in VSCode.

## Communication to the measurement process

### Use case - GUI

- The GUI has to stop the measurement
- The GUI has to restart the measurement
  - Stop the measurement
  - Wait till the measurement finished
  - Start a new measurement

### Communication mechanisms

- File `tmp_filelock_lock.txt`
  - The measurement creates this files and locks it.
  - A) The measurement deletes the file at exit
  - B) The GUI tries to delete the file: If the file may be deleted, the measurement has quit
- File `tmp_filelock_status.txt` (Future - not implemented now)
  - The measurement creates this file
  - Content:
    - `MEASURING`
    - `STOPPING`
    - `STOPPED_SUCCESS`
    - `STOPPED_ERROR`
- File `tmp_filelock_stop_hard.txt`
- File `tmp_filelock_stop_soft.txt`
  - The measurement creates these files and does NOT lock them.
  - When the GUI removes this file, the measurement will stop.
  - The measurement deletes the files at exit.
