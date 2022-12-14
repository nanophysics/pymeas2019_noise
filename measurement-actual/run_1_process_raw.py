import pathlib
import logging

# pylint: disable=wrong-import-position
import library_path

library_path.init(__file__)

import config_measurement  # pylint: disable=wrong-import-position

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent
DIR_MEASUREMENT = library_path.DIR_MEASUREMENT


from pymeas import library_logger
from pymeas import program_instrument_capture_raw
from pymeas import library_topic
from pymeas import program
from pymeas.program_configsetup import ConfigSetup

logger = logging.getLogger("logger")

skip_on_error = False


def patch_configsetup(configsetup) -> ConfigSetup:
    configsetup.validate()
    configsetup.unlock()
    configsetup.module_instrument = program_instrument_capture_raw
    configsetup.capture_raw_hit_anykey = False
    configsetup.validate()
    return configsetup


def main():
    library_logger.init_logger_condense(DIR_MEASUREMENT)

    configsetup = patch_configsetup(config_measurement.get_configsetup())

    for dir_raw in program.iter_dir_raw(dir_measurement=DIR_MEASUREMENT):
        try:
            pickles = list(dir_raw.glob("densitystep_*.pickle"))
            if len(pickles) > 0:
                logger.info(f"directory '{dir_raw.name}' already processed: processing SKIPPED")
                continue
            configsetup.measure(dir_measurement=DIR_MEASUREMENT, dir_raw=dir_raw, do_exit=False)
        except library_topic.FrequencyNotFound as e:
            if skip_on_error:
                logger.warning(f"SKIPPED: {e}")
                continue
            raise

    # logger.info("Now process as 'run_1_condense.py'!")
    # plot_config = config_plot.get_plot_config()
    # program.run_condense(dir_measurement=DIR_MEASUREMENT, plot_config=plot_config, skip_on_error=True)
    # run_2_composite_plots.run(dir_measurement=DIR_MEASUREMENT)


if __name__ == "__main__":
    main()
