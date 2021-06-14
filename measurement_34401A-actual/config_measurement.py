TITLE = "Noise Demo Title"


def get_configsetup():
    from pymeas import program_config_instrument_keysight34401A

    config = program_config_instrument_keysight34401A.get_config_setupKeysight34401A()

    config.step_3_slow.duration_s = 30.0 * 24.0 * 3600.0
    config.step_3_slow.input_Vp = program_config_instrument_keysight34401A.InputRangeKeysight34401A.RANGE_100mV   # RANGE_100mV, RANGE_1V, RANGE_10V, RANGE_100V, RANGE_1000V
    #config.step_3_slow.skalierungsfaktor = 1.0e-3

    return config
