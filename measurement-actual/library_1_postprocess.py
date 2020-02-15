import math
import pathlib

def postprocess(dir_raw):
    isinstance(dir_raw, pathlib.Path)
    # evaluate flicker noise
    filename = dir_raw.joinpath('result_presentation.txt')
    with filename.open('r') as fin:
        dict_file = eval(fin.read())

    PS = dict_file['presentations']['PS']

    f_low = 0.1
    f_high = 10.0
    P_sum = 0.0
    n = 0
    for f, p in zip(PS['x'], PS['y']):
        if f > f_low:
            P_sum += p
            n += 1
            if f > f_high - 1e-3:
                break
    if n != 24:
        print( f'Flickernoise: not enough values to calculate.' )
        return
    flicker_noise_Vrms = math.sqrt(P_sum)
    print( f'Flickernoise: 0.1 Hz to 10 Hz is {flicker_noise_Vrms:0.3E} Vrms' )
