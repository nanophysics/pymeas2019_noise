# The user can use a postprocess to evaluate the quality of a device for example.
# Just delete this file if no need for postprocess
# The example shows the calculation of flicker noise 0.1 ... 10 Hz
# The measurement time could be set to 60s for example.
# Just start run_0_measure.bat and observe the result

import logging
import pathlib

logger = logging.getLogger("logger")


def postprocess(dir_measurement, plotData):
    isinstance(dir_measurement, pathlib.Path)

    with (dir_measurement / "result_flickernoise.txt").open("w") as f:
        f.write(f"Flickernoise: 0.1 ... 10 Hz\n")
        f.write(f"{'Topic':50s}\t{'Vrms':8s}\t{'Vrms-BASENOISE':8s}\tcomment\n")
        for topic in plotData.list_topics:
            flickernoise_Vrms, flickernoise_minus_basenoise_Vrms, comment = topic.flickernoise()
            f.write(f"{topic.topic:50s}\t{flickernoise_Vrms:8.3e}\t{flickernoise_minus_basenoise_Vrms:8.3e}\t{comment}\n")

    # flicker_noise_Vrms = math.sqrt(P_sum)
    # flicker_noise_limit_Vrms = 1.0e-6
    # logger.info("")
    # logger.info(f"Flickernoise: 0.1 Hz to 10 Hz is {flicker_noise_Vrms:0.3E} Vrms")
    # if flicker_noise_Vrms < flicker_noise_limit_Vrms:
    #     logger.info(f"This flickernoise is below the limit of {flicker_noise_limit_Vrms:0.3E} Vrms")
    #     logger.info("Good component")
    # else:
    #     logger.warning(f"This flickernoise is above the limit of {flicker_noise_limit_Vrms:0.3E} Vrms")
    #     logger.warning(f"Bad component")
