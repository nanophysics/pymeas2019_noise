TITLE = "Zenerdiode noise"


def get_configsetup():
    from pymeas import program_config_instrument_picoscope

    config = program_config_instrument_picoscope.get_config_setupPS500A()

    duration_slow_s = 48 * 3600.0
    config.step_0_settle.settle_time_ok_s = 40.00
    config.step_0_settle.duration_s = config.step_0_settle.settle_time_ok_s + 4 * 60.0
    config.step_0_settle.settle_input_part = 0.5
    config.step_3_slow.duration_s = duration_slow_s
    for step in config.configsteps:
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        step.input_Vp = program_config_instrument_picoscope.InputRange.R_100mV
        # step.input_Vp = program_config_instrument_picoscope.InputRange.R_500mV
        step.skalierungsfaktor = 1.0e-3

    # config.step_0_settle.skip = True
    # config.step_1_fast.skip = True
    # config.step_2_medium.skip = True
    # config.step_3_slow.skip = True

    return config
