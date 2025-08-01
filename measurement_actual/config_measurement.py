from pymeas2019_noise.constants_ad_low_noise_float_2023 import (
    ConfigStepAdLowNoiseFloat2023,
    RegisterFilter1,
    RegisterMux,
)
from pymeas2019_noise.program_configsetup import ConfigSetup

TITLE = "Noise"


def get_configsetup() -> ConfigSetup:
    from pymeas2019_noise import program_config_instrument_ad_low_noise_float_2023

    config = program_config_instrument_ad_low_noise_float_2023.get_config_setup()
    config.filename = __file__
    # config.capture_raw = True
    # config.capture_raw_hit_anykey = True

    config.step_0_settle.settle_time_ok_s = 2.00
    config.step_0_settle.duration_s = config.step_0_settle.settle_time_ok_s + 5.0
    config.step_0_settle.settle_input_part = 0.5

    assert isinstance(config.step_3_slow, ConfigStepAdLowNoiseFloat2023)
    config.step_3_slow.duration_s = 7 * 24.0 * 3600.0
    config.step_3_slow.register_filter1 = RegisterFilter1.SPS_97656
    # 'additional_SPI_reads' creates additional noise on the SPI tracks

    # config.step_3_slow.additional_SPI_reads = int(
    #     RegisterFilter1.SPS_97656.SPS / config.step_3_slow.register_filter1.SPS
    # )

    config.step_3_slow.update_dt_s()
    config.step_3_slow.register_mux = RegisterMux.NORMAL_INPUT_POLARITY
    for step in config.configsteps:
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        step.skalierungsfaktor = 1.0

    return config
