TITLE = "Noise Demo Title"


def get_configsetup():
    from pymeas import program_config_instrument_keysight34401A

    config = program_config_instrument_keysight34401A.get_config_setupKeysight34401A()


    return config
