# The user can use a postprocess to evaluate the quality of a device for example.
# Just delete this file if no need for postprocess
# The example shows the calculation of flicker noise 0.1 ... 10 Hz
# The measurement time could be set to 60s for example.
# Just start run_0_measure.bat and observe the result

import math
import logging
import pathlib
from library_measurement import Measurement

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
            # TODO: Move to data class
            self.list_results.sort(key=lambda m: (m.measurement_date, m.measurement_type, m.subtype, m.channel2))
            for result in self.list_results:
                result.writeline(f)

    def voltage(self, measurement):
        assert isinstance(measurement, Measurement)
        measured_V = measurement.measurement_channel_voltage.read()
        if measured_V is None:
            logger.warning(f"{measurement.combination}: NO VOLTAGE")
            return False
        logger.debug(f"{measurement.combination}: Voltage {measured_V}")
        limit_V, tol_V = measurement.combination.limit_V
        # min < meas < max, %
        diff_V = limit_V - measured_V
        self.list_results.append(Line(
            measurement_date=self.dir_measurement_date.name,
            measurement_type=measurement.combination.dirpart_measurementtype,
            subtype="DC voltage",
            channel=measurement.combination.channel,
            unit="V",
            min=limit_V-tol_V,
            max=limit_V+tol_V,
            measured=measured_V,
        ))

    def flickernoise(self, measurement):
        assert isinstance(measurement, Measurement)
        dir_raw = measurement.dir_measurement_channel
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

        flickernoise_Vrms = math.sqrt(P_sum)
        limit_flickernoise_min_Vrms, limit_flickernoise_max_Vrms = measurement.combination.limit_flickernoise_Vrms
        comment = ""
        if n != 24:
            flickernoise_Vrms = 42.0
            comment = "Flickernoise: not enough values to calculate."

        # if n != 24:
        #     logger.warning("Flickernoise: not enough values to calculate.")
        #     return
        # flickernoise_Vrms = math.sqrt(P_sum)
        # flicker_noise_limit_Vrms = 1.0e-6
        # logger.debug("")
        # logger.debug(f"Flickernoise: 0.1 Hz to 10 Hz is {flickernoise_Vrms:0.3E} Vrms")
        # if flickernoise_Vrms < flicker_noise_limit_Vrms:
        #     logger.debug(f"This flickernoise is below the limit of {flicker_noise_limit_Vrms:0.3E} Vrms")
        #     logger.debug("Good component")
        # else:
        #     logger.warning(f"This flickernoise is above the limit of {flicker_noise_limit_Vrms:0.3E} Vrms")
        #     logger.warning(f"Bad component")

        self.list_results.append(Line(
            measurement_date=self.dir_measurement_date.name,
            measurement_type=measurement.combination.dirpart_measurementtype,
            subtype="Flickernoise",
            channel=measurement.combination.channel,
            unit="Vrms",
            min=limit_flickernoise_min_Vrms,
            max=limit_flickernoise_max_Vrms,
            measured=flickernoise_Vrms,
            comment=comment,
        ))
