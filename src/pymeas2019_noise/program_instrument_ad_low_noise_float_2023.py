# https://github.com/petermaerki/ad_low_noise_float_2023_git/blob/hmaerki/evaluation_software/evaluation_software/cpp_cdc/2025-03-30a_ads127L21/src/reader.py
import logging
import sys

import ad_low_noise_float_2023
from ad_low_noise_float_2023.ad import AdLowNoiseFloat2023
from ad_low_noise_float_2023.constants import PcbParams

from . import program_configsetup
from .constants_ad_low_noise_float_2023 import ConfigStepAdLowNoiseFloat2023
from .library_filelock import ExitCode
from .program_fir import UniformPieces

logger = logging.getLogger("logger")

REQUIRED_PACKAGE_VERSION = "0.0.3"
"""
Required version of python package 'ad_low_noise_float_2023'
"""


class Instrument:
    def __init__(self, configstep: ConfigStepAdLowNoiseFloat2023):
        assert isinstance(configstep, ConfigStepAdLowNoiseFloat2023)

        if ad_low_noise_float_2023.__version__ < REQUIRED_PACKAGE_VERSION:
            msg = f"Found '{ad_low_noise_float_2023.__version__}' but required at least '{REQUIRED_PACKAGE_VERSION}'!"
            logger.error(msg)
            raise ValueError(msg)
   
        self.configstep = configstep
        self.adc = AdLowNoiseFloat2023()

    def acquire(
        self,
        configstep: program_configsetup.ConfigStep,
        filename_capture_raw,
        stream_output,
        filelock_measurement,
    ):  # pylint: disable=too-many-statements
        assert isinstance(configstep, program_configsetup.ConfigStep)
        assert isinstance(stream_output, UniformPieces)

        total_samples = int(configstep.duration_s / configstep.dt_s)
        pcb_params = PcbParams(scale_factor=configstep.skalierungsfaktor)

        stream_output.init(stage=0, dt_s=configstep.dt_s)

        def flush_stages():
            max_calculations = 30
            for _ in range(max_calculations):
                calculation_stage = stream_output.push(None)
                done = len(calculation_stage) == 0
                if done:
                    break

        def stop(exit_code: ExitCode, reason: str):
            assert isinstance(exit_code, ExitCode)
            assert isinstance(reason, str)
            stream_output.put_EOF(exit_code=exit_code)
            logger.info(f"STOP({reason})")

        def out_of_sync() -> None:
            logger.info("out_of_sync")

        for measurements in self.adc.iter_measurements_V(
            pcb_params=pcb_params,
            total_samples=total_samples,
            cb_out_of_sync=out_of_sync,
        ):
            if filelock_measurement.requested_stop_soft():
                return stop(ExitCode.CTRL_C, "<ctrl-c> or softstop")
            queueFull = stream_output.push(measurements.adc_value_V)
            assert not queueFull

        flush_stages()
        return stop(ExitCode.OK, "time over")


def main():
    print(f"Started: {sys.version}")
    instrument = Instrument(configstep=None)
    instrument.connect(pcb_params=PcbParams())

    instrument.adc.test_usb_speed()
    return
    for i, adc_value_ain_V in enumerate(instrument.adc.iter_measurements()):
        if i % 100 == 0:
            print(f"{adc_value_ain_V[0]=:1.6f}")

    # instrument.adc.cb_measurement = cb_measurement


if __name__ == "__main__":
    main()
