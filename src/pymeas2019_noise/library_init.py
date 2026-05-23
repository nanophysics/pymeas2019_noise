"""
This file will be called from the github action to
create a measurement_actual.zip file.
"""

import dataclasses
import logging
import pathlib
import shutil
import sys

logger = logging.getLogger("logger")

DIRECTORY_MEASUREMENT_ACTUAL = pathlib.Path.cwd() / "measurement_actual"

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
IS_LINUX = sys.platform.startswith("linux")

COMMANDS: list[str] = [
    "run_0_measure",
    "run_0_gui",
    "run_1_condense",
    "run_1_process_raw",
    "run_2_composite_plots",
]


@dataclasses.dataclass(slots=True, repr=True, frozen=True)
class Target:
    content: str
    is_linux: bool
    dev: bool

    @property
    def filename_suffix(self) -> str:
        return ".sh" if self.is_linux else ".bat"


_TARGETS: list[Target] = [
    Target(
        content=r"""
uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- pymeas2019 <COMMAND> @args
echo ERRORLEVEL %ERRORLEVEL%
pause
""".strip(),
        dev=False,
        is_linux=False,
    ),
    Target(
        content=r"""
rem This script assumes: uv pip install -e .[dev]
pymeas2019 <COMMAND> @args
echo ERRORLEVEL %ERRORLEVEL%
pause
""".strip(),
        dev=True,
        is_linux=False,
    ),
    Target(
        content=r"""
#!/usr/bin/env bash
# You may need to add the execution bit: chmod a+x *.sh
set -eu

uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- pymeas2019 <COMMAND> "$@"
""".strip(),
        dev=False,
        is_linux=True,
    ),
    Target(
        content=r"""
#!/usr/bin/env bash
# You may need to add the execution bit: chmod a+x *.sh
# This script assumes: uv pip install -e .[dev]
set -eu

pymeas2019 <COMMAND> "$@"
# uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- pymeas2019 <COMMAND> "$@"
""".strip(),
        dev=True,
        is_linux=True,
    ),
]


def get_target(dev: bool) -> Target:
    for target in _TARGETS:
        if target.is_linux == IS_LINUX:
            if target.dev == dev:
                return target
    raise NotImplementedError("Target not found - Programming error!")


def init(
    directory_measurement_actual: pathlib.Path,
    dev: bool,
    force: bool,
) -> None:
    if directory_measurement_actual.is_dir():
        if force:
            shutil.rmtree(path=directory_measurement_actual)
            logger.error(f"Directory removed: '{directory_measurement_actual.name}'")
        else:
            logger.error(
                f"Directory already exists: '{directory_measurement_actual.name}'. Remove the directory and try again!"
            )
            return
    directory_measurement_actual.mkdir(parents=True)
    logger.info(f"directory created: '{directory_measurement_actual.name}'")
    logger.info(
        f"You may now 'cd' in this directory and start 'run_0_gui.{'sh' if IS_LINUX else 'bat'}'"
    )
    target = get_target(dev=dev)
    for command in COMMANDS:
        content = target.content.replace("<COMMAND>", command)
        filename = directory_measurement_actual / f"{command}{target.filename_suffix}"
        filename.write_text(content)
        if filename.suffix == ".sh":
            filename.chmod(0o755)

    for filename in (DIRECTORY_OF_THIS_FILE / "config_templates").glob("*.py"):
        content = filename.read_text()
        (directory_measurement_actual / filename.name).write_text(content)


if __name__ == "__main__":
    init(
        directory_measurement_actual=DIRECTORY_MEASUREMENT_ACTUAL,
        dev=False,
        force=False,
    )
