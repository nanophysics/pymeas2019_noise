import logging
import pathlib
from pymeas import program_configsetup

# pylint: disable=wrong-import-position
from . import library_logger
from . import library_filelock
from . import program

logger = logging.getLogger("logger")


def measure(configsetup, dir_measurement):
    assert isinstance(configsetup, program_configsetup.ConfigSetup)
    assert isinstance(dir_measurement, pathlib.Path)

    dir_raw = program.examine_dir_raw(dir_measurement=dir_measurement)

    library_logger.init_logger_measurement(directory=dir_raw)

    logger.info(configsetup.info)
    configsetup.measure(dir_measurement=dir_measurement, dir_raw=dir_raw)

    library_filelock.FilelockMeasurement.update_status(f"Condense data: {dir_raw.name}")

    program.run_condense_dir_raw(dir_raw=dir_raw, do_plot=False)