TITLE = "Noise Demo Title"


def get_configsetup():
    from pymeas import program_config_instrument_keysight34401A

    config = program_config_instrument_keysight34401A.get_config_setupKeysight34401A()

    config.step_3_slow.duration_s = 30.0 * 24.0 * 3600.0

    return config
