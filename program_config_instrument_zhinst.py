import enum
import math

import program_instrument_zhinst

# sample frequencies and fir_counts
f0_fast_fs_hz = 125e6  # do not change this values as this is the fastest rate with 15 bit
f1_medium_fs_hz = f0_fast_fs_hz / float(2 ** 1)  # do not change this values as this is the fastest rate with 16 bit
exponent_slow = 5  # free to change. Peter has choosen 5 on his laptop
f2_slow_fs_hz = f0_fast_fs_hz / float(2 ** exponent_slow)
f1_medium_useful_hz = 20e6 / 3.0  # 3 dB frequency is 20 Mhz
# print(f'f1_medium_useful_hz wanted  : {f1_medium_useful_hz:.0f} Hz')
temp = int(round(math.log(f0_fast_fs_hz / f1_medium_useful_hz, 2)))
f1_medium_useful_hz = f0_fast_fs_hz / 2 ** temp
# print(f'f1_medium_useful_hz selected: {f1_medium_useful_hz:.0f} Hz')
f0_fast_fir_count_skipped = 0  # fixed: we do not want to skip any. Due to nyquist criterion we could see some spurious signals for frequencies above.
f0_fast_fir_count = int(round(math.log(f0_fast_fs_hz / f1_medium_useful_hz, 2)))
# input B filter
R_filter_input_B_ohm = 10000.0
C_filter_input_B_farad = 1e-9
fg_filter_input_B = 1.0 / (2.0 * math.pi * R_filter_input_B_ohm * C_filter_input_B_farad)
# print(f'fg_filter_input_B: {fg_filter_input_B:.0f} Hz')
f2_slow_useful_hz = fg_filter_input_B / 3.0
# print(f'f2_slow_useful_hz wanted  : {f2_slow_useful_hz:.0f} Hz')
f1_medium_fir_count = int(round(math.log(f1_medium_fs_hz / f2_slow_useful_hz, 2)))
f2_slow_useful_hz = f1_medium_fs_hz / 2 ** f1_medium_fir_count
f1_medium_fir_count_skipped = int(round(math.log(f1_medium_fs_hz / f1_medium_useful_hz, 2)))
# print(f'f2_slow_useful_hz selected  : {f2_slow_useful_hz:.0f} Hz')
f2_slow_fir_count_skipped = int(round(math.log(f2_slow_fs_hz / f2_slow_useful_hz, 2)))
fir_count_2_slow = f2_slow_fir_count_skipped + 27  # free to choose


def get_config_setupPS500A(inputRange, duration_slow_s, skalierungsfaktor):
    assert isinstance(inputRange, float)
    assert isinstance(duration_slow_s, float)
    assert isinstance(skalierungsfaktor, float)

    dict_config_setup = dict(
        setup_name="Measure",
        module_instrument=program_instrument_zhinst,
        steps=(
            dict(
                stepname="0_fast",
                # External
                skalierungsfaktor=skalierungsfaktor,
                # Processing
                fir_count=f0_fast_fir_count,
                fir_count_skipped=f0_fast_fir_count_skipped,  # highest frequencies get skipped
                # Picoscope
                input_channel="A",  # channel A is connected without filter to the amplifier out
                input_Vp=inputRange,
                bandwitdth="BW_20MHZ",
                offset=0.0,
                resolution="15bit",
                duration_s=3600.0,  #  Memory will limit time (7s)
                dt_s=1.0 / f0_fast_fs_hz,
            ),
            dict(
                stepname="1_medium",
                # External
                skalierungsfaktor=skalierungsfaktor,
                # Processing
                fir_count=f1_medium_fir_count,
                fir_count_skipped=f1_medium_fir_count_skipped,
                # Picoscope
                input_channel="A",  # channel A is connected without filter to the amplifier out
                input_Vp=inputRange,
                bandwitdth="BW_20MHZ",
                offset=0.0,
                resolution="16bit",
                duration_s=3600.0,  #  Memory will limit time (9.7s)
                dt_s=1.0 / f1_medium_fs_hz,
            ),
            dict(
                stepname="2_slow",
                # External
                skalierungsfaktor=skalierungsfaktor,
                # Processing
                fir_count=fir_count_2_slow,
                fir_count_skipped=f2_slow_fir_count_skipped,
                # Picoscope
                input_channel="B",  # channel B is connected with filter low pass 100 kHz ??? to the amplifier out
                input_Vp=inputRange,
                bandwitdth="BW_20MHZ",
                offset=0.0,
                resolution="16bit",
                # duration_s = 60.0,
                duration_s=duration_slow_s,
                dt_s=1 / f2_slow_fs_hz,
            ),
        ),
    )

    return dict_config_setup
