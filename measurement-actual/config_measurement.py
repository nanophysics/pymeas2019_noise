TITLE = "Noise Demo Title"


def get_dict_config_setup():
    import program_config_instrument_picoscope

    dict_config_setup = program_config_instrument_picoscope.get_config_setupPS500A(
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        inputRange=program_config_instrument_picoscope.InputRange.R_100mV,
        duration_slow_s=48 * 3600.0,
        skalierungsfaktor=1.0e-3,
    )
    return dict_config_setup
