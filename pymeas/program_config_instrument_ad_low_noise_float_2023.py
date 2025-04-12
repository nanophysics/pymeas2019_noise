import enum
import logging

from . import program_instrument_ad_low_noise_float_2023
from .program_configsetup import ConfigSetup, ConfigStep, ConfigStepSkip

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


f2_settle_fs_hz = 1000.0
fir_count_3_slow = 20
f2_slow_fs_hz = 195313.0


def get_config_setup() -> ConfigSetup:  # pylint: disable=too-many-statements
    setup = ConfigSetup()
    setup.setup_name = "Measure"
    setup.module_instrument = program_instrument_ad_low_noise_float_2023

    # step = setup.step_0_settle = ConfigStep()
    step = setup.step_0_settle = ConfigStepSkip()
    step.stepname = "0_settle"
    step.settle = True
    step.input_channel = "A"
    step.bandwidth = "BW_20MHZ"
    step.offset = 0.0
    step.resolution = "16bit"
    step.dt_s = 1 / f2_settle_fs_hz

    step = setup.step_1_fast = ConfigStepSkip()
    step.stepname = "1_fast"

    step = setup.step_2_medium = ConfigStepSkip()
    step.stepname = "2_medium"

    step = setup.step_3_slow = ConfigStep()
    step.stepname = "3_slow"
    step.fir_count = fir_count_3_slow
    step.bandwidth = "BW_20MHZ"
    step.offset = 0.0
    step.resolution = "16bit"
    step.dt_s = 1 / f2_slow_fs_hz
    step.input_channel = "A"

    return setup
