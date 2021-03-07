import logging

from pymeas import library_logger
from library_combinations import Combinations, Speed
from library_measurement import Measurement
import library_qualification

logger = logging.getLogger("logger")


class MeasurementController:
    def __init__(self, context):
        self.context = context
        self.init_logger()

    def init_logger(self):
        # create file handler which logs even debug messages
        self.context.dir_measurements.mkdir(parents=True, exist_ok=True)
        library_logger.init_logger_append(self.context.dir_measurements / "logger_measurements.txt", fmt="%(asctime)s %(levelname)7s %(message)s")

    def run(self) -> None:
        with self.context.stati as stati:
            self.run_measurements()
            self.run_qualifikation()

    def run_measurements(self) -> None:
        logger.info("****** run_measurements()")
        logger.info(f"context.dir_measurement_date: {self.context.dir_measurement_date}")
        if self.context.speed != Speed.DETAILED:
            logger.warning(f"context.speed: {self.context.speed.name}")
        for device in ("picoscope", "voltmeter", "scanner", "compact"):
            name = f"mocked_{device}"
            mocked = getattr(self.context, name)
            if mocked:
                logger.warning(f"context.{name}: MOCKED")

        for combination in Combinations(speed=self.context.speed):
            # print(combination)
            with Measurement(self.context, combination) as measurement:
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
                        measurement.plot()
                        stati.commit()

    def run_qualifikation(self) -> None:
        logger.info("****** run_qualifikation()")
        for combination in Combinations(speed=self.context.speed):
            # print(combination)
            with Measurement(self.context, combination) as measurement:
                library_qualification.postprocess_voltage(measurement=measurement)
                library_qualification.postprocess(measurement.dir_measurement_channel)
