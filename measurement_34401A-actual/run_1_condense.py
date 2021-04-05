import sys
import logging

import library_path

library_path.init(__file__)

# pylint: disable=wrong-import-position
from pymeas import library_logger
from pymeas import program

import run_2_composite_plots

logger = logging.getLogger("logger")

DIR_MEASUREMENT = library_path.DIR_MEASUREMENT


def reload_if_changed(dir_raw):
    return program.reload_if_changed(dir_raw=dir_raw)


def run():
    library_logger.init_logger_condense(DIR_MEASUREMENT)

    if len(sys.argv) > 1:
        dir_raw = sys.argv[1]
        if dir_raw == "TOPONLY":
            logger.info(f"Argument '{dir_raw}': run_2_composite_plots.run('{DIR_MEASUREMENT}')")
            run_2_composite_plots.run(dir_measurement=DIR_MEASUREMENT)
            return
        logger.info(f"Argument '{dir_raw}': program.run_condense_dir_raw('{DIR_MEASUREMENT / dir_raw}')")
        program.run_condense_dir_raw(dir_raw=DIR_MEASUREMENT / dir_raw)
        return

    logger.info(f"No arguments': run_condense('{DIR_MEASUREMENT}')")
    program.run_condense(dir_measurement=DIR_MEASUREMENT)
    run_2_composite_plots.run(dir_measurement=DIR_MEASUREMENT)


if __name__ == "__main__":
    run()
