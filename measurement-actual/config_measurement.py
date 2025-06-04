from pymeas.program_configsetup import ConfigSetup
from pymeas.constants_ad_low_noise_float_2023 import (
    InputRangeADLowNoiseFloat2023,
    RegisterFilter1,
    RegisterMux,
    ConfigStepAdLowNoiseFloat2023,
)

TITLE = "Noise"


def get_configsetup() -> ConfigSetup:
    from pymeas import program_config_instrument_ad_low_noise_float_2023

    config = program_config_instrument_ad_low_noise_float_2023.get_config_setup()
    config.filename = __file__
    # config.capture_raw = True
    # config.capture_raw_hit_anykey = True

    config.step_0_settle.settle_time_ok_s = 2.00
    config.step_0_settle.duration_s = config.step_0_settle.settle_time_ok_s + 5.0
    config.step_0_settle.settle_input_part = 0.5

    assert isinstance(config.step_3_slow, ConfigStepAdLowNoiseFloat2023)
    config.step_3_slow.duration_s = 10.0 * 3600.0
    config.step_3_slow.register_filter1 = RegisterFilter1.SPS_03052
    config.step_3_slow.update_dt_s()
    config.step_3_slow.register_mux = RegisterMux.NORMAL_INPUT_POLARITY
    for step in config.configsteps:
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        step.input_Vp = InputRangeADLowNoiseFloat2023.RANGE_5000mV_gain_1
        step.skalierungsfaktor = 1.0

    return config
