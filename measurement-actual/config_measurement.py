from pymeas.program_configsetup import ConfigSetup

TITLE = "Noise"


def get_configsetup() -> ConfigSetup:
    from pymeas import program_config_instrument_ad_low_noise_float_2023

    config = program_config_instrument_ad_low_noise_float_2023.get_config_setup()
    config.filename = __file__
    # config.capture_raw = True
    # config.capture_raw_hit_anykey = True

    config.step_0_settle.settle_time_ok_s = 5.00
    config.step_0_settle.duration_s = config.step_0_settle.settle_time_ok_s + 5.0
    config.step_0_settle.settle_input_part = 0.5

    config.step_3_slow.duration_s = 60.0
    for step in config.configsteps:
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        step.input_Vp = (
            program_config_instrument_ad_low_noise_float_2023.InputRangeADLowNoiseFloat2023.RANGE_5V
        )
        # step.input_Vp = program_config_instrument_picoscope.InputRange.R_500mV
        step.skalierungsfaktor = 1.0e-3

    # config.step_0_settle.skip = True
    # config.step_1_fast.skip = True
    # # config.step_2_medium.skip = True
    # # config.step_3_slow.skip = True

    return config
