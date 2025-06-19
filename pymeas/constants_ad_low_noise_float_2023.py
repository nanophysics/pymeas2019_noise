from __future__ import annotations

import dataclasses
import enum

from .program_configsetup import ConfigStep


class RegisterFilter1(enum.IntEnum):
    """
    https://github.com/petermaerki/ad_low_noise_float_2023_git/blob/main/components/ad/ADS127L21.pdf
    CLK 25 MHz
    """

    # SPS_390625 = 0x00  # Not supported
    # SPS_195313 = 0x01  # Not supported
    SPS_97656 = 0x02
    SPS_48828 = 0x03
    SPS_24414 = 0x04
    SPS_12207 = 0x05
    SPS_06104 = 0x06
    SPS_03052 = 0x07

    @property
    def SPS(self) -> int:
        return {
            self.SPS_97656: 97656,
            self.SPS_48828: 48828,
            self.SPS_24414: 24414,
            self.SPS_12207: 12207,
            self.SPS_06104: 6104,
            self.SPS_03052: 3052,
        }[self]


class RegisterMux(enum.IntEnum):
    """
    https://github.com/petermaerki/ad_low_noise_float_2023_git/blob/main/components/ad/ADS127L21.pdf
    """

    NORMAL_INPUT_POLARITY = 0b00
    INVERTED_INPUT_POLARITY = 0b01
    OFFSET_AND_NOISE_TEST = 0b10
    COMMON_MODE_TEST = 0b11


REFP_V = 5.0
AD_FS_V = REFP_V
GAIN_J2 = 2.0
GAIN_J5 = 5.0
GAIN_J10 = 10.0


class InputRangeADLowNoiseFloat2023(enum.Enum):
    RANGE_500mV_gain_10_J10 = "500"
    RANGE_1000mV_gain_5_J5 = "1000"
    RANGE_2500mV_gain_2_J2 = "2500"
    RANGE_5000mV_gain_1 = "5000"

    @property
    def V(self) -> float:
        return {
            InputRangeADLowNoiseFloat2023.RANGE_500mV_gain_10_J10: AD_FS_V / GAIN_J10,
            InputRangeADLowNoiseFloat2023.RANGE_1000mV_gain_5_J5: AD_FS_V / GAIN_J5,
            InputRangeADLowNoiseFloat2023.RANGE_2500mV_gain_2_J2: AD_FS_V / GAIN_J2,
            InputRangeADLowNoiseFloat2023.RANGE_5000mV_gain_1: AD_FS_V,
        }[self]


@dataclasses.dataclass(slots=True)
class ConfigStepAdLowNoiseFloat2023(ConfigStep):
    register_filter1: RegisterFilter1 = RegisterFilter1.SPS_97656
    register_mux: RegisterMux = RegisterMux.NORMAL_INPUT_POLARITY
    additional_SPI_reads: int = 0

    def __post_init__(self) -> None:
        self.update_dt_s()

    def update_dt_s(self) -> None:
        """
        Muss immer aufgerufen werden, nachdem register_filter1 gesetzt wurde.
        """
        self.dt_s = 1.0 / self.register_filter1.SPS
