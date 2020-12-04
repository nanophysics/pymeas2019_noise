TITLE = "Noise Demo Title"


def get_configsetup():
    from pymeas import program_config_instrument_picoscope

    config = program_config_instrument_picoscope.get_config_setupPS500A()

    duration_slow_s = 48 * 3600.0
    config.step_0_settle.settle_time_ok_s = duration_slow_s
    config.step_0_settle.duration_s = 30.0 * duration_slow_s
    config.step_0_settle.settle_input_part = 0.5
    for step in config.configsteps:
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        step.input_Vp = program_config_instrument_picoscope.InputRange.R_100mV
        step.skalierungsfaktor = 1.0e-3
    return config
