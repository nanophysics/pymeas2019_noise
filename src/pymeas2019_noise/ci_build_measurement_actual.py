"""
This file will be called from the github action to
create a measurement_actual.zip file.
"""

import dataclasses
import pathlib
import zipfile

DIRECTORY_ARTIFACTS = "artifacts"
DIRECTORY_MEASUREMENT_ACTUAL = "measurement_actual"
FILENAME_MEASUREMENT_ACTUAL_ZIP = f"{DIRECTORY_MEASUREMENT_ACTUAL}_<TARGET>.zip"

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

COMMANDS: list[str] = [
    "run_0_measure",
    "run_0_plot_interactive",
    "run_1_condense",
    "run_1_process_raw",
    "run_2_composite_plots",
]


@dataclasses.dataclass(slots=True, repr=True, frozen=True)
class Target:
    label: str
    content: str
    filename_suffix: str


TARGETS: list[Target] = [
    Target(
        label="windows",
        content=r"""
uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python -m pymeas2019_noise.<COMMAND>
echo ERRORLEVEL %ERRORLEVEL%
pause
        """.strip(),
        filename_suffix=".bat",
    ),
    Target(
        label="windows_dev",
        content=r"""
..\venv\Scripts\python.exe -m pymeas2019_noise.<COMMAND>
echo ERRORLEVEL %ERRORLEVEL%
pause
        """.strip(),
        filename_suffix=".bat",
    ),
    Target(
        label="linux_dev",
        content=r"""
set -eu

../venv/bin/python -m pymeas2019_noise.<COMMAND>

# uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python -m pymeas2019_noise.<COMMAND>
        """.strip(),
        filename_suffix=".sh",
    ),
]


def main() -> None:
    directory_measurement_actual = (
        DIRECTORY_OF_THIS_FILE.parent.parent / DIRECTORY_MEASUREMENT_ACTUAL
    )
    assert directory_measurement_actual.is_dir(), str(DIRECTORY_MEASUREMENT_ACTUAL)

    directory_artifacts = pathlib.Path.cwd() / DIRECTORY_ARTIFACTS
    directory_artifacts.mkdir(parents=True, exist_ok=True)
    for target in TARGETS:
        filename_zip = directory_artifacts / FILENAME_MEASUREMENT_ACTUAL_ZIP.replace(
            "<TARGET>", target.label
        )
        with zipfile.ZipFile(filename_zip, "w") as zipf:
            for command in COMMANDS:
                content = target.content.replace("<COMMAND>", command)
                filename = (
                    f"{DIRECTORY_MEASUREMENT_ACTUAL}/{command}{target.filename_suffix}"
                )
                zipf.writestr(filename, content)

            for pattern in ("*.py", "*.ps1"):
                for config_file in directory_measurement_actual.glob(pattern):
                    filename = f"{DIRECTORY_MEASUREMENT_ACTUAL}/{config_file.name}"
                    zipf.writestr(filename, config_file.read_text())


if __name__ == "__main__":
    main()
