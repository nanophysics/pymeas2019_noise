# The user can use a postprocess to evaluate the quality of a device for example.
# Just delete this file if no need for postprocess
# The example shows the calculation of flicker noise 0.1 ... 10 Hz
# The measurement time could be set to 60s for example.
# Just start run_0_measure.bat and observe the result

import math
import logging
import pathlib

from library_qualification_data import Line

logger = logging.getLogger("logger")


class Qualification:
    def __init__(self, dir_measurement_date: pathlib.Path):
        assert isinstance(dir_measurement_date, pathlib.Path)
        self.dir_measurement_date = dir_measurement_date
        self.list_results = []

    def write_qualification(self):
        file_qualification = self.dir_measurement_date / "result_qualification.csv"
        with file_qualification.open("w") as f:
            Line.writeheader(f)
            for result in self.list_results:
                result.writeline(f)

    def voltage(self, measurement):
        measured_V = measurement.measurement_channel_voltage.read()
        if measured_V is None:
            logger.warning(f"{measurement.combination}: NO VOLTAGE")
            return False
        logger.info(f"{measurement.combination}: Voltage {measured_V}")
        expected_V, tol_V = measurement.combination.expected_V
        logger.info(expected_V)
        # min < meas < max, %
        diff_V = expected_V - measured_V
        diff_relative = diff_V / tol_V
        logger.info(f"{measured_V:0.3}V {diff_relative*100.0:0.0f}% ({expected_V:0.3f}+/-{tol_V:0.3f}V)")
        self.list_results.append(Line(
            measurement_date=self.dir_measurement_date.name,
            measurement_type=measurement.combination.dirpart_measurementtype,
            channel=measurement.combination.channel,
            unit="V",
            min=expected_V-tol_V,
            max=expected_V+tol_V,
            measured=measured_V
        ))
        return True

    def postprocess(self, dir_raw):
        isinstance(dir_raw, pathlib.Path)
        # evaluate flicker noise
        filename = dir_raw / "result_presentation.txt"
        with filename.open("r") as fin:
            dict_file = eval(fin.read())  # pylint: disable=eval-used

        PS = dict_file["presentations"]["PS"]

        f_low = 0.1
        f_high = 10.0
        P_sum = 0.0
        n = 0
        for f, p in zip(PS["x"], PS["y"]):
            if f > f_low:
                P_sum += p
                n += 1
                if f > f_high - 1e-3:
                    break
        if n != 24:
            logger.warning("Flickernoise: not enough values to calculate.")
            return
        flicker_noise_Vrms = math.sqrt(P_sum)
        flicker_noise_limit_Vrms = 1.0e-6
        logger.info("")
        logger.info(f"Flickernoise: 0.1 Hz to 10 Hz is {flicker_noise_Vrms:0.3E} Vrms")
        if flicker_noise_Vrms < flicker_noise_limit_Vrms:
            logger.info(f"This flickernoise is below the limit of {flicker_noise_limit_Vrms:0.3E} Vrms")
            logger.info("Good component")
        else:
            logger.warning(f"This flickernoise is above the limit of {flicker_noise_limit_Vrms:0.3E} Vrms")
            logger.warning(f"Bad component")
