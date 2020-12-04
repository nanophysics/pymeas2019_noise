import logging

import library_path

TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()

# pylint: disable=wrong-import-position
import library_logger
import library_filelock
import config_measurement
import program

logger = logging.getLogger("logger")


def run():
    dir_raw = program.examine_dir_raw(dir_measurement=DIR_MEASUREMENT)

    library_logger.init_logger_measurement(directory=dir_raw)

    configsetup = config_measurement.get_configsetup()
    configsetup.validate()
    logger.info(configsetup.info)
    configsetup.measure(dir_measurement=DIR_MEASUREMENT, dir_raw=dir_raw)

    library_filelock.FilelockMeasurement.update_status(f"Condense data: {dir_raw.name}")

    program.run_condense_dir_raw(dir_raw=dir_raw, do_plot=False)


if __name__ == "__main__":
    run()
