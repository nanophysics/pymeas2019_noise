import time
import logging

from pymeas import library_logger
from library_combinations import Combinations, Speed
from library_measurement import Measurement
import library_qualification

logger = logging.getLogger("logger")


class MeasurementController:
    def __init__(self, context):
        self.context = context
        self.start_s = time.time()
        self.init_logger()

    def init_logger(self):
        # create file handler which logs even debug messages
        self.context.dir_measurements.mkdir(parents=True, exist_ok=True)
        library_logger.init_logger_append(self.context.dir_measurements / "logger_measurements.txt", fmt="%(asctime)s %(levelname)7s %(message)s")

    def run(self) -> None:
        with self.context.stati as stati:
            self.run_measurements()
            self.run_qualifikation()

    def print_duration(self) -> None:
        logger.info(f"Duration: {time.time()-self.start_s:0.0f}s")

    def run_measurements(self) -> None:
        logger.info("****** run_measurements()")
        logger.info(f"context.dir_measurement_date: {self.context.dir_measurement_date}")
        if (self.context.speed != Speed.DETAILED_NO_HV_AMP) or (self.context.speed != Speed.DETAILED_WITH_HV_AMP):
            logger.warning(f"context.speed: {self.context.speed.name}")
        for device in ("picoscope", "voltmeter", "scanner", "compact"):
            name = f"mocked_{device}"
            mocked = getattr(self.context, name)
            if mocked:
                logger.warning(f"context.{name}: MOCKED")

        for combination in Combinations(speed=self.context.speed):
            # print(combination)
            with Measurement(self.context, combination) as measurement:
                try:
                    with measurement.stati_meastype_channel_noise as stati:
                        if stati.requires_to_run:
                            measurement.create_directory()
                            measurement.connect_pyboards()
                            measurement.configure(voltage=True)
                            measurement.measure_voltage()
                            measurement.configure(density=True)
                            measurement.measure_density()
                            if not self.context.mocked_picoscope:
                                stati.commit()

                    with measurement.stati_meastype_channel_plot as stati:
                        if stati.requires_to_run:
                            measurement.channel_plot()
                            stati.commit()

                    with measurement.stati_meastype_plot as stati:
                        if stati.requires_to_run:
                            measurement.meastype_plot()
                            stati.commit()
                except Exception as e:  # pylint: disable=broad-except
                    logger.exception(e)

    def run_qualifikation(self) -> None:
        logger.info("****** run_qualifikation()")

        qualification = library_qualification.Qualification(dir_measurement_date=self.context.dir_measurement_date)
        for combination in Combinations(speed=self.context.speed):
            # print(combination)
            with Measurement(self.context, combination) as measurement:
                qualification.qualify_using_calc(measurement=measurement)
        qualification.write_qualification()
