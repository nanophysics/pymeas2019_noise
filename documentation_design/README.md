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
