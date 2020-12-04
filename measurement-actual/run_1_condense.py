import pathlib

import library_path

TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()

# pylint: disable=wrong-import-position
import library_logger
import program
import run_2_composite_plots


def reload_if_changed(dir_raw):
    return program.reload_if_changed(dir_raw=dir_raw)


def run():
    library_logger.init_logger_condense(DIR_MEASUREMENT)

    program.run_condense(dir_measurement=DIR_MEASUREMENT)
    run_2_composite_plots.run(dir_measurement=DIR_MEASUREMENT)


if __name__ == "__main__":
    run()
