import logging
import pathlib

# pylint: disable=wrong-import-position
from . import (
    library_filelock,
    library_logger,
    library_plot_config,
    program,
    program_configsetup,
)

logger = logging.getLogger("logger")


def measure2(configsetup: program_configsetup.ConfigSetup, dir_raw: pathlib.Path):
    program.create_or_empty_directory(dir_raw=dir_raw)
    configsetup.backup(dir_raw=dir_raw)

    library_logger.init_logger_measurement(directory=dir_raw)

    configsetup.measure(dir_measurement=dir_raw.parent, dir_raw=dir_raw)

    library_filelock.FilelockMeasurement.update_status(f"Condense data: {dir_raw.name}")

    plot_config_dummy = library_plot_config.PlotConfig(
        eseries="E12",
        unit="V",
        integral_index_start=0.1,
    )
    program.run_condense_dir_raw(
        dir_raw=dir_raw, do_plot=False, plot_config=plot_config_dummy
    )


def measure(configsetup, dir_measurement: pathlib.Path, subdir_raw: str):
    assert isinstance(configsetup, program_configsetup.ConfigSetup)
    assert isinstance(dir_measurement, pathlib.Path)
    assert isinstance(subdir_raw, str)

    dir_raw = program.examine_dir_raw(
        dir_measurement=dir_measurement,
        subdir_raw=subdir_raw,
    )

    measure2(configsetup, dir_raw)
