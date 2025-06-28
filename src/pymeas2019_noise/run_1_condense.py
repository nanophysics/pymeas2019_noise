import logging
import pathlib
import sys

import config_plot

from . import library_logger, program, run_2_composite_plots

logger = logging.getLogger("logger")

def reload_if_changed(dir_raw):
    plot_config = config_plot.get_plot_config()
    return program.reload_if_changed(dir_raw=dir_raw, plot_config=plot_config)


def doit(dir_measurement:pathlib.Path):
    plot_config = config_plot.get_plot_config()

    if len(sys.argv) > 1:
        dir_raw = sys.argv[1]
        if dir_raw == "TOPONLY":
            logger.info(
                f"Argument '{dir_raw}': run_2_composite_plots.run('{dir_measurement}')"
            )
            run_2_composite_plots.run(dir_measurement=dir_measurement)
            return
        logger.info(
            f"Argument '{dir_raw}': program.run_condense_dir_raw('{dir_measurement / dir_raw}')"
        )
        program.run_condense_dir_raw(
            dir_raw=dir_measurement / dir_raw, plot_config=plot_config
        )
        return

    logger.info(f"No arguments': run_condense('{dir_measurement}')")
    program.run_condense(
        dir_measurement=dir_measurement, plot_config=plot_config, skip_on_error=True
    )
    run_2_composite_plots.run(dir_measurement=dir_measurement)

def main():
    dir_measurement = pathlib.Path.cwd()

    library_logger.init_logger_condense(dir_measurement)

    doit(dir_measurement=dir_measurement)

if __name__ == "__main__":
    main()
