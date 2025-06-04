import logging

from . import program_instrument_ad_low_noise_float_2023
from .program_configsetup import ConfigSetup, ConfigStepSkip
from .constants_ad_low_noise_float_2023 import (
    ConfigStepAdLowNoiseFloat2023,
    RegisterFilter1,
    RegisterMux,
)

logger = logging.getLogger("logger")


fir_count_3_slow = 20


def get_config_setup() -> ConfigSetup:  # pylint: disable=too-many-statements
    setup = ConfigSetup()
    setup.setup_name = "Measure"
    setup.module_instrument = program_instrument_ad_low_noise_float_2023

    step = setup.step_0_settle = ConfigStepSkip()
    step.stepname = "0_settle"
    step.settle = True
    step.input_channel = "B"  # old, picoscope
    step.bandwidth = "BW_20MHZ"  # old, picoscope
    step.offset = 0.0
    step.resolution = "16bit"  # old, picoscope

    step = setup.step_1_fast = ConfigStepSkip()
    step.stepname = "1_fast"

    step = setup.step_2_medium = ConfigStepSkip()
    step.stepname = "2_medium"

    step = setup.step_3_slow = ConfigStepAdLowNoiseFloat2023(
        register_filter1=RegisterFilter1.SPS_97656,
        register_mux=RegisterMux.NORMAL_INPUT_POLARITY,
    )
    step.stepname = "3_slow"
    step.fir_count = fir_count_3_slow
    step.bandwidth = "BW_20MHZ"  # old, picoscope
    step.offset = 0.0
    step.resolution = "16bit"  # old, picoscope
    step.input_channel = "A"

    return setup
