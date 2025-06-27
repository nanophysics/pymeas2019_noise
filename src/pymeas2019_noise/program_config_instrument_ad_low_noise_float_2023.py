import logging

from . import program_instrument_ad_low_noise_float_2023
from .constants_ad_low_noise_float_2023 import (
    ConfigStepAdLowNoiseFloat2023,
    RegisterFilter1,
    RegisterMux,
)
from .program_configsetup import ConfigSetup, ConfigStepSkip

logger = logging.getLogger("logger")


fir_count_3_slow = 30


def get_config_setup() -> ConfigSetup:  # pylint: disable=too-many-statements
    setup = ConfigSetup()
    setup.setup_name = "Measure"
    setup.module_instrument = program_instrument_ad_low_noise_float_2023

    step0 = setup.step_0_settle = ConfigStepSkip()
    step0.stepname = "0_settle"
    step0.settle = True
    step0.input_channel = "B"  # old, picoscope
    step0.bandwidth = "BW_20MHZ"  # old, picoscope
    step0.offset = 0.0
    step0.resolution = "16bit"  # old, picoscope

    step1 = setup.step_1_fast = ConfigStepSkip()
    step1.stepname = "1_fast"

    step2 = setup.step_2_medium = ConfigStepSkip()
    step2.stepname = "2_medium"

    step3 = setup.step_3_slow = ConfigStepAdLowNoiseFloat2023(
        register_filter1=RegisterFilter1.SPS_97656,
        register_mux=RegisterMux.NORMAL_INPUT_POLARITY,
    )
    step3.stepname = "3_slow"
    step3.fir_count = fir_count_3_slow
    step3.bandwidth = "BW_20MHZ"  # old, picoscope
    step3.offset = 0.0
    step3.resolution = "16bit"  # old, picoscope
    step3.input_channel = "A"

    return setup
