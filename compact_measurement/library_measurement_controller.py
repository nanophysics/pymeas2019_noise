import logging

import library_path
from library_combinations import Combinations
from library_measurement import Measurement

TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()

from pymeas import library_logger  # pylint: disable=wrong-import-position

logger = logging.getLogger(library_logger.LOGGER_NAME)


class MeasurementController:
    def __init__(self, context):
        self.context = context
        self.init_logger()

    def init_logger(self):
        # create file handler which logs even debug messages
        self.context.dir_measurements.mkdir(parents=True, exist_ok=True)
        library_logger.init_logger_append(self.context.dir_measurements / 'logger_measurements.txt')

    def run_measurements(self):
        logger.info('****** run_measurements()')
        logger.info(f'  context.dir_measurement_date: {self.context.dir_measurement_date}')
        logger.info(f'  context.speed: {self.context.speed.name}')
        logger.info(f'  context.mocked_scanner: {self.context.mocked_scanner}')
        logger.info(f'  context.mocked_compact: {self.context.mocked_compact}')

        for combination in Combinations(speed=self.context.speed):
            # print(combination)
            with Measurement(self.context, combination) as measurement:
                if measurement.stati_measurement.requires_to_run:
                    logger.info(f'    {measurement.dir_measurement_channel.relative_to(self.context.dir_measurements)}')
                    measurement.stati_measurement.reset()
                    measurement.create_directory()
                    measurement.connect_pyboards()
                    measurement.configure()
                    measurement.measure()
                    if not self.context.mocked_picoscope:
                        measurement.stati_measurement.commit()

                if measurement.stati_plot.requires_to_run:
                    measurement.plot()
                    measurement.stati_plot.commit()

    def run_qualifikation(self):
        logger.info('    run_qualifikation()')

    def run_diagrams(self):
        logger.info('    run_diagrams()')
