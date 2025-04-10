import math
import logging
import enum

from .program_configsetup import ConfigSetup, ConfigStep
from . import program_instrument_ad_low_noise_float_2023
logger = logging.getLogger("logger")


class InputRangeADLowNoiseFloat2023(enum.Enum):
    RANGE_1V = "1"
    RANGE_5V = "5"

    @property
    def V(self):
        return {
            InputRangeADLowNoiseFloat2023.RANGE_1V: 1.0,
            InputRangeADLowNoiseFloat2023.RANGE_5V: 5.0,
        }[self]
    
# sample frequencies and fir_counts
f0_fast_fs_hz = 125e6  # do not change this values as this is the fastest rate with 15 bit
f1_medium_fs_hz = f0_fast_fs_hz / float(2 ** 1)  # do not change this values as this is the fastest rate with 16 bit
exponent_slow = 5  # free to change. Peter has choosen 5 on his laptop
f2_slow_fs_hz = f0_fast_fs_hz / float(2 ** exponent_slow)
f1_medium_useful_hz = 20e6 / 3.0  # 3 dB frequency is 20 Mhz
# logger.debug(f'f1_medium_useful_hz wanted  : {f1_medium_useful_hz:.0f} Hz')
temp = int(round(math.log(f0_fast_fs_hz / f1_medium_useful_hz, 2)))
f1_medium_useful_hz = f0_fast_fs_hz / 2 ** temp
# logger.debug(f'f1_medium_useful_hz selected: {f1_medium_useful_hz:.0f} Hz')
f0_fast_fir_count_skipped = 0  # fixed: we do not want to skip any. Due to nyquist criterion we could see some spurious signals for frequencies above.
f0_fast_fir_count = int(round(math.log(f0_fast_fs_hz / f1_medium_useful_hz, 2)))
# input B filter
R_filter_input_B_ohm = 10000.0
C_filter_input_B_farad = 1e-9
fg_filter_input_B = 1.0 / (2.0 * math.pi * R_filter_input_B_ohm * C_filter_input_B_farad)
# logger.debug(f'fg_filter_input_B: {fg_filter_input_B:.0f} Hz')
f2_slow_useful_hz = fg_filter_input_B / 3.0
# logger.debug(f'f2_slow_useful_hz wanted  : {f2_slow_useful_hz:.0f} Hz')
f1_medium_fir_count = int(round(math.log(f1_medium_fs_hz / f2_slow_useful_hz, 2)))
f2_slow_useful_hz = f1_medium_fs_hz / 2 ** f1_medium_fir_count
f1_medium_fir_count_skipped = int(round(math.log(f1_medium_fs_hz / f1_medium_useful_hz, 2)))
# logger.debug(f'f2_slow_useful_hz selected  : {f2_slow_useful_hz:.0f} Hz')
f2_slow_fir_count_skipped = int(round(math.log(f2_slow_fs_hz / f2_slow_useful_hz, 2)))
fir_count_2_slow = f2_slow_fir_count_skipped + 27  # free to choose

exponent_settle = 17  # free to change.
f2_settle_fs_hz = f0_fast_fs_hz / float(2 ** exponent_settle)

exponent_settle = 21  # 59 Hz
exponent_settle = 19  # 238 Hz
f2_settle_fs_hz = f0_fast_fs_hz / float(2 ** exponent_settle)


def get_config_setup() -> ConfigSetup:  # pylint: disable=too-many-statements
    setup = ConfigSetup()
    setup.setup_name = "Measure"
    setup.module_instrument = program_instrument_ad_low_noise_float_2023

    step = ConfigStep()
    step.stepname = "0_settle"
    step.settle = True
    # step.settle_time_ok_s = ...
    # step.settle_input_part = ...
    # External
    # step.skalierungsfaktor = ...
    # Picoscope
    step.input_channel = "A"  # channel A is connected without filter to the amplifier out
    # step.input_Vp = ...
    step.bandwidth = "BW_20MHZ"
    step.offset = 0.0
    step.resolution = "16bit"
    # step.duration_s = ...
    step.dt_s = 1 / f2_settle_fs_hz
    setup.step_0_settle = step

    step = ConfigStep()
    step.stepname = "1_fast"
    # External
    # step.skalierungsfaktor = ...
    # Processing
    step.fir_count = f0_fast_fir_count
    step.fir_count_skipped = f0_fast_fir_count_skipped  # highest frequencies get skipped
    # Picoscope
    step.input_channel = "A"  # channel A is connected without filter to the amplifier out
    # step.input_Vp = ...
    step.bandwidth = "BW_20MHZ"
    step.offset = 0.0
    step.resolution = "15bit"
    step.duration_s = 0.6  #  Memory will limit time (7s). After about 0.5s the usb transfer starts and adds additional noise
    step.dt_s = 1.0 / f0_fast_fs_hz
    setup.step_1_fast = step

    step = ConfigStep()
    step.stepname = "2_medium"
    # External
    # step.skalierungsfaktor = ...
    # Processing
    step.fir_count = f1_medium_fir_count
    step.fir_count_skipped = f1_medium_fir_count_skipped
    # Picoscope
    step.input_channel = "A"  # channel A is connected without filter to the amplifier out
    # step.input_Vp = ...
    step.bandwidth = "BW_20MHZ"
    step.offset = 0.0
    step.resolution = "16bit"
    step.duration_s = 3.0  #  Memory will limit time (9.7s)
    step.dt_s = 1.0 / f1_medium_fs_hz
    setup.step_2_medium = step

    step = ConfigStep()
    step.stepname = "3_slow"
    # External
    # step.skalierungsfaktor = ...
    # Processing
    step.fir_count = fir_count_2_slow
    step.fir_count_skipped = f2_slow_fir_count_skipped
    # Picoscope
    step.input_channel = "B"  # channel B is connected with filter low pass 100 kHz ??? to the amplifier out
    # step.input_Vp = ...
    step.bandwidth = "BW_20MHZ"
    step.offset = 0.0
    step.resolution = "16bit"
    step.duration_s = 60.0
    step.dt_s = 1 / f2_slow_fs_hz
    setup.step_3_slow = step

    return setup
