import logging
import pathlib

import config_measurement

from . import (
    library_logger,
    library_topic,
    program,
    program_instrument_capture_raw,
)
from .program_configsetup import ConfigSetup

logger = logging.getLogger("logger")

skip_on_error = False


def patch_configsetup(configsetup) -> ConfigSetup:
    configsetup.validate()
    configsetup.unlock()
    configsetup.module_instrument = program_instrument_capture_raw
    configsetup.capture_raw_hit_anykey = False
    configsetup.validate()
    return configsetup


def doit(dir_measurement:pathlib.Path):
    configsetup = patch_configsetup(config_measurement.get_configsetup())

    for dir_raw in program.iter_dir_raw(dir_measurement=dir_measurement):
        try:
            pickles = list(dir_raw.glob("densitystep_*.pickle"))
            if len(pickles) > 0:
                logger.info(
                    f"directory '{dir_raw.name}' already processed: processing SKIPPED"
                )
                continue
            configsetup.measure(
                dir_measurement=dir_measurement, dir_raw=dir_raw, do_exit=False
            )
        except library_topic.FrequencyNotFound as e:
            if skip_on_error:
                logger.warning(f"SKIPPED: {e}")
                continue
            raise

    # logger.info("Now process as 'run_1_condense.py'!")
    # plot_config = config_plot.get_plot_config()
    # program.run_condense(dir_measurement=DIR_MEASUREMENT, plot_config=plot_config, skip_on_error=True)
    # run_2_composite_plots.run(dir_measurement=DIR_MEASUREMENT)


def main():
    dir_measurement = pathlib.Path.cwd()

    library_logger.init_logger_condense(dir_measurement)

    doit(dir_measurement=dir_measurement)

if __name__ == "__main__":
    main()
