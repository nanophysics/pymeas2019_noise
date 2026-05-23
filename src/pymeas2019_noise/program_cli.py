import logging
import os
import pathlib
import sys

import typer
import typing_extensions

from . import library_topic

ENABLE_IRRELEVANT_COMMANDS = False


# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing_extensions.Annotated

logger = logging.getLogger("logger")

app = typer.Typer()

cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)


def init_logger() -> None:
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)


@app.command(help="Create initial folder 'measurement-actual'")
def init(
    force: typing_extensions.Annotated[
        bool,
        typer.Option(
            help="Remove existing directory and create a new one",
        ),
    ] = False,
    dev: typing_extensions.Annotated[
        bool,
        typer.Option(
            help="Install development scripts (using uv)",
        ),
    ] = False,
):
    from . import library_init

    init_logger()
    library_init.init(
        directory_measurement_actual=library_init.DIRECTORY_MEASUREMENT_ACTUAL,
        dev=dev,
        force=force,
    )


if ENABLE_IRRELEVANT_COMMANDS:

    @app.command()
    def run0_gui_wxwidgets():
        from . import run_0_gui_wxwidgets

        run_0_gui_wxwidgets.main()


@app.command(
    name="run_0_gui",
    help="Open the GUI",
)
def run0_gui():
    from . import run_0_gui

    run_0_gui.main()


@app.command(
    name="run_0_measure",
    help="Start a measurement (TODO: Add options)",
)
def run0_measure(
    subdir_raw: typing_extensions.Annotated[
        str,
        typer.Option(
            help="The subdirectory with the raw measurement data",
        ),
    ] = library_topic.ResultAttributes.result_dir_default(),
):
    from . import run_0_measure

    run_0_measure.main(subdir_raw=subdir_raw)


@app.command(
    name="run_0_measure_synthetic",
    help="Create measurement from synthetic data.",
)
def run0_measure_synthetic():
    from . import run_0_measure_synthetic

    run_0_measure_synthetic.main()


@app.command(
    name="run_1_condense",
    help="condense existing measurements",
)
def run1_condense():
    from . import run_1_condense

    run_1_condense.main()


if ENABLE_IRRELEVANT_COMMANDS:

    @app.command(name="run_1_process_raw_0")
    def run1_process_raw0():
        from . import run_1_process_raw_0

        run_1_process_raw_0.main()


@app.command(
    name="run_1_process_raw",
    help="TODO: Add correct help text",
)
def run1_process_raw():
    from . import run_1_process_raw

    run_1_process_raw.main()


@app.command(
    name="run_2_composite_plots",
    help="TODO: Add correct help text",
)
def run2_composite_plots():
    from . import run_2_composite_plots

    run_2_composite_plots.main(dir_measurement=pathlib.Path.cwd())


if __name__ == "__main__":
    app()
