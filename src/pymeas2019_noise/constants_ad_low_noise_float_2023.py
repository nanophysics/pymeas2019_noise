from __future__ import annotations

import dataclasses

from ad_low_noise_float_2023.constants import RegisterFilter1, RegisterMux

from .program_configsetup import ConfigStep


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
