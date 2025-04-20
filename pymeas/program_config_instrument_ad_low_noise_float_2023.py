import enum
import logging

from . import program_instrument_ad_low_noise_float_2023
from .program_configsetup import ConfigSetup, ConfigStep, ConfigStepSkip

logger = logging.getLogger("logger")


class InputRangeADLowNoiseFloat2023(enum.Enum):
    RANGE_500mV = "500"
    RANGE_1000mV = "1000"
    RANGE_2500mV = "2500"
    RANGE_5000mV = "5000"

    @property
    def V(self) -> float:
        return {
            InputRangeADLowNoiseFloat2023.RANGE_500mV: 0.5,
            InputRangeADLowNoiseFloat2023.RANGE_1000mV: 1.0,
            InputRangeADLowNoiseFloat2023.RANGE_2500mV: 2.5,
            InputRangeADLowNoiseFloat2023.RANGE_5000mV: 5.0,
        }[self]


# fs_hz = 195313.0  # CLK 25 MHz
# fs_hz = 3052.0  # CLK 25 MHz
fs_hz = 24_414.0  # CLK 25 MHz
fir_count_3_slow = 20


def get_config_setup() -> ConfigSetup:  # pylint: disable=too-many-statements
    setup = ConfigSetup()
    setup.setup_name = "Measure"
    setup.module_instrument = program_instrument_ad_low_noise_float_2023

    step = setup.step_0_settle = ConfigStep()
    step = setup.step_0_settle = ConfigStepSkip()
    step.stepname = "0_settle"
    step.settle = True
    step.input_channel = "B" # old, picoscope
    step.bandwidth = "BW_20MHZ" # old, picoscope
    step.offset = 0.0
    step.resolution = "16bit" # old, picoscope
    step.dt_s = 1 / fs_hz

    step = setup.step_1_fast = ConfigStepSkip()
    step.stepname = "1_fast"

    step = setup.step_2_medium = ConfigStepSkip()
    step.stepname = "2_medium"

    step = setup.step_3_slow = ConfigStep()
    step.stepname = "3_slow"
    step.fir_count = fir_count_3_slow
    step.bandwidth = "BW_20MHZ" # old, picoscope
    step.offset = 0.0
    step.resolution = "16bit" # old, picoscope
    step.dt_s = 1 / fs_hz
    step.input_channel = "A"

    return setup
