"""
This file will be called from the github action to
create a measurement_actual.zip file.
"""

import dataclasses
import pathlib
import sys
import zipfile

DIRECTORY_ARTIFACTS = "artifacts"
DIRECTORY_MEASUREMENT_ACTUAL = "measurement_actual"
FILENAME_MEASUREMENT_ACTUAL_ZIP = f"{DIRECTORY_MEASUREMENT_ACTUAL}_<TARGET>.zip"

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
    label: str
    content: str
    is_linux: bool
    is_development: bool

    @property
    def filename_suffix(self) -> str:
        return ".sh" if self.is_linux else ".bat"


TARGETS: list[Target] = [
    Target(
        label="windows",
        content=r"""
uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python -m pymeas2019_noise.<COMMAND>
echo ERRORLEVEL %ERRORLEVEL%
pause
        """.strip(),
        is_development=False,
        is_linux=False,
    ),
    Target(
        label="windows_dev",
        content=r"""
..\venv\Scripts\python.exe -m pymeas2019_noise.<COMMAND>
echo ERRORLEVEL %ERRORLEVEL%
pause
        """.strip(),
        is_development=True,
        is_linux=False,
    ),
    Target(
        label="linux_dev",
        content=r"""
set -eu

../venv/bin/python -m pymeas2019_noise.<COMMAND>

# uv run --with=git+https://github.com/nanophysics/pymeas2019_noise.git -- python -m pymeas2019_noise.<COMMAND>
        """.strip(),
        is_development=True,
        is_linux=True,
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

                if target.is_linux == IS_LINUX:
                    filename1 = (
                        directory_measurement_actual
                        / f"{command}{target.filename_suffix}"
                    )
                    filename1.write_text(content)
                    if IS_LINUX:
                        filename1.chmod(0o755)

            for pattern in ("*.py", "*.ps1"):
                for config_file in directory_measurement_actual.glob(pattern):
                    filename = f"{DIRECTORY_MEASUREMENT_ACTUAL}/{config_file.name}"
                    zipf.writestr(filename, config_file.read_text())


if __name__ == "__main__":
    main()
