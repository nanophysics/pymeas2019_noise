import socket

TITLE = "Noise Demo Title"


SETTLE_TIME_OK_S = 100.0

IS_COMPUTER_DEVELOPMENT = socket.gethostname() in ("maerki-lenovo",)
if IS_COMPUTER_DEVELOPMENT:
    SETTLE_TIME_OK_S = 5.0

def get_configsetup():
    import program_config_instrument_picoscope

    return program_config_instrument_picoscope.get_config_setupPS500A(
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        inputRange=program_config_instrument_picoscope.InputRange.R_100mV,
        duration_slow_s=48 * 3600.0,
        skalierungsfaktor=1.0e-3,
        settle_time_ok_s=SETTLE_TIME_OK_S
    )
