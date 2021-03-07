import logging

from pymeas import library_logger
from library_combinations import Combinations
from library_measurement import Measurement

logger = logging.getLogger('logger')

class MeasurementController:
    def __init__(self, context):
        self.context = context
        self.init_logger()

    def init_logger(self):
        # create file handler which logs even debug messages
        self.context.dir_measurements.mkdir(parents=True, exist_ok=True)
        library_logger.init_logger_append(self.context.dir_measurements / 'logger_measurements.txt', fmt="%(asctime)s %(levelname)5s %(message)s")

    def run(self):
        with self.context.stati as stati:
            self.run_measurements()
            self.run_qualifikation()
            self.run_diagrams()

    def run_measurements(self):
        logger.info('****** run_measurements()')
        logger.info(f'  context.dir_measurement_date: {self.context.dir_measurement_date}')
        logger.info(f'  context.speed: {self.context.speed.name}')
        logger.info(f'  context.mocked_scanner: {self.context.mocked_scanner}')
        logger.info(f'  context.mocked_compact: {self.context.mocked_compact}')

        for combination in Combinations(speed=self.context.speed):
            # print(combination)
            with Measurement(self.context, combination) as measurement:
                with measurement.stati_meastype_channel_noise as stati:
                    if stati.requires_to_run:
                        measurement.create_directory()
                        measurement.connect_pyboards()
                        measurement.configure()
                        measurement.measure()
                        if not self.context.mocked_picoscope:
                            stati.commit()

                with measurement.stati_meastype_channel_plot as stati:
                    if stati.requires_to_run:
                        measurement.plot()
                        stati.commit()

    def run_qualifikation(self):
        logger.info('    run_qualifikation()')

    def run_diagrams(self):
        logger.info('    run_diagrams()')
