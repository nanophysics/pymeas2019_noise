import enum
import logging
import math

from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

from . import program_instrument_picoscope5442D
from .program_configsetup import ConfigSetup, ConfigStep

logger = logging.getLogger("logger")


class InputRange(enum.IntEnum):
    R_10mV_do_not_use = PS5000ARange.R_10MV  # do not use! use 100mV range instead (noise of picoscope is similar in 100mV range)
    R_20mV_do_not_use = PS5000ARange.R_20MV  #  do not use! use 100mV range instead (noise of picoscope is similar in 100mV range)
    R_50mV_do_not_use = PS5000ARange.R_50MV  # do not use! use 100mV range instead (noise of picoscope is similar in 100mV range)
    R_100mV = PS5000ARange.R_100MV  # good range     # low noise of picoscope
    R_200mV = PS5000ARange.R_200MV
    R_500mV = PS5000ARange.R_500MV  #  big increase of picoscope noise compared to 200 mV range
    R_1V = PS5000ARange.R_1V
    R_2V = PS5000ARange.R_2V
    R_5V = PS5000ARange.R_5V
    R_10V = PS5000ARange.R_10V
    R_20V = PS5000ARange.R_20V
    R_50V = PS5000ARange.R_50V

    @property
    def V(self):
        return {
            InputRange.R_100mV: 0.1,
            InputRange.R_200mV: 0.2,
            InputRange.R_500mV: 0.5,
            InputRange.R_1V: 1.0,
            InputRange.R_2V: 2.0,
            InputRange.R_5V: 5.0,
            InputRange.R_10V: 10.0,
            InputRange.R_20V: 20.0,
            InputRange.R_50V: 50.0,
        }[self.value]


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


def get_config_setupPS500A() -> ConfigSetup:  # pylint: disable=too-many-statements
    setup = ConfigSetup()
    setup.setup_name = "Measure"
    setup.module_instrument = program_instrument_picoscope5442D

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
