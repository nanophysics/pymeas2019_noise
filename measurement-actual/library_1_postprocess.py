# The user can use a postprocess to evaluate the quality of a device for example.
# Just delete this file if no need for postprocess
# The example shows the calculation of flicker noise 0.1 ... 10 Hz
# The measurement time could be set to 60s for example.
# Just start run_0_measure.bat and observe the result

import math
import pathlib


def postprocess(dir_raw):
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
        print(f"Flickernoise: not enough values to calculate.")
        return
    flicker_noise_Vrms = math.sqrt(P_sum)
    flicker_noise_limit_Vrms = 1.0e-6
    print("")
    print(f"Flickernoise: 0.1 Hz to 10 Hz is {flicker_noise_Vrms:0.3E} Vrms")
    if flicker_noise_Vrms < flicker_noise_limit_Vrms:
        print(f"This flickernoise is below the limit of {flicker_noise_limit_Vrms:0.3E} Vrms")
        print(f"Good component")
    else:
        print(f"This flickernoise is above the limit of {flicker_noise_limit_Vrms:0.3E} Vrms")
        print(f"Bad component")
