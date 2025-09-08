import dataclasses
import enum
import logging
import pathlib
import types
from collections.abc import Iterable

from ad_low_noise_float_2023.constants import AD_FS_V, PcbParams

from . import program_fir
from .library_filelock import ExitCode, FilelockMeasurement
from .program_lockingmixin_mock import LockingMixinMock, TO_BE_SET

LockingMixin = LockingMixinMock

logger = logging.getLogger("logger")


@dataclasses.dataclass(slots=True)
class SamplingProcessConfig(LockingMixinMock):
    fir_count: int = 0
    fir_count_skipped: int = 0
    stepname: str = TO_BE_SET
    settle: bool = False
    settle_time_ok_s: float = None
    settle_input_part: float = None
    skalierungsfaktor: float = 1.0
    input_Vp: float = 1.0
    duration_s: float = TO_BE_SET

    def validate(self):
        assert isinstance(self.fir_count, int)
        assert isinstance(self.fir_count_skipped, int)
        assert isinstance(self.stepname, str)
        assert isinstance(self.settle, bool)
        assert isinstance(self.settle_time_ok_s, None | float)
        assert isinstance(self.settle_input_part, None | float)
        if self.settle:
            assert isinstance(self.settle_time_ok_s, float)
            assert isinstance(self.settle_input_part, float)
        assert isinstance(self.skalierungsfaktor, float)
        assert isinstance(self.input_Vp, float)
        assert isinstance(self.duration_s, float)

        self._freeze()


@dataclasses.dataclass(slots=True)
class ConfigStep(LockingMixinMock):
    stepname: str = TO_BE_SET
    settle: bool = False
    settle_time_ok_s: float = None
    settle_input_part: float = None
    skalierungsfaktor: float = TO_BE_SET
    fir_count: int = 0
    fir_count_skipped: int = 0
    input_channel: str = TO_BE_SET
    input_internal_Vp: float | None = None
    """
    None if provided by the instrument.
    """
    bandwidth: str = TO_BE_SET
    offset: float = TO_BE_SET
    resolution: str = TO_BE_SET
    duration_s: float = TO_BE_SET
    dt_s: float = TO_BE_SET
    skip: bool = False

    @property
    def input_Vp(self) -> float:
        if isinstance(self.input_internal_Vp, enum.Enum):
            return self.input_internal_Vp.V
        assert isinstance(self.input_internal_Vp, float)
        return self.input_internal_Vp

    def validate(self):
        assert isinstance(self.stepname, str)
        assert isinstance(self.settle, bool)
        assert isinstance(self.settle_time_ok_s, None | float)
        assert isinstance(self.settle_input_part, None | float)
        if self.settle:
            assert isinstance(self.settle_time_ok_s, float)
            assert isinstance(self.settle_input_part, float)
        assert isinstance(self.skalierungsfaktor, float)
        assert isinstance(self.fir_count, int)
        assert isinstance(self.fir_count_skipped, int)
        assert isinstance(self.input_channel, str)
        assert isinstance(self.input_internal_Vp, enum.Enum | float | None)
        assert isinstance(self.bandwidth, str)
        assert isinstance(self.offset, float)
        assert isinstance(self.resolution, str)
        assert isinstance(self.duration_s, float)
        assert isinstance(self.dt_s, float)
        assert isinstance(self.skip, bool)

        self._freeze()

    @property
    def process_config(self):
        c = SamplingProcessConfig()
        c.fir_count = self.fir_count
        c.fir_count_skipped = self.fir_count_skipped
        c.stepname = self.stepname
        c.settle = self.settle
        c.settle_time_ok_s = self.settle_time_ok_s
        c.settle_input_part = self.settle_input_part
        c.skalierungsfaktor = self.skalierungsfaktor
        c.input_Vp = self.input_Vp
        c.duration_s = self.duration_s

        return c

    def get_filename_capture_raw(
        self, config_setup: "ConfigSetup", dir_raw: pathlib.Path
    ) -> pathlib.Path | None:
        if config_setup.capture_raw:
            return dir_raw / f"capture_raw_{self.stepname}.raw"
        return None


class ConfigStepSkip(ConfigStep):
    def __init__(self) -> None:
        super().__init__()
        self.skalierungsfaktor: float = 42.0
        self.input_channel: str = "42"
        self.input_internal_Vp = None
        self.bandwidth: str = "42"
        self.offset: float = 42.0
        self.resolution: str = "42"
        self.duration_s: float = 42.0
        self.dt_s: float = 42.0
        self.skip: bool = True


@dataclasses.dataclass(slots=True)
class ConfigSetup(LockingMixin):  # pylint: disable=too-few-public-methods
    filename: str = None
    setup_name: str = TO_BE_SET
    module_instrument: types.ModuleType = TO_BE_SET
    capture_raw: bool = False
    "Save the datastream from the scope directly to a file and do not process it."
    capture_raw_hit_anykey: bool = False
    step_0_settle: ConfigStep = TO_BE_SET
    step_1_fast: ConfigStep = TO_BE_SET
    step_2_medium: ConfigStep = TO_BE_SET
    step_3_slow: ConfigStep = TO_BE_SET

    def __post_init__(self):
        pass

    def validate(self):
        assert isinstance(self.filename, None | str)
        assert isinstance(self.setup_name, str)
        assert isinstance(self.module_instrument, types.ModuleType)
        assert isinstance(self.capture_raw, bool)
        assert isinstance(self.step_0_settle, ConfigStep)
        assert isinstance(self.step_1_fast, ConfigStep)
        assert isinstance(self.step_2_medium, ConfigStep)
        assert isinstance(self.step_3_slow, ConfigStep)

        self._freeze()

        for configstep in self.configsteps:
            configstep.validate()

    def backup(self, dir_raw):
        if self.filename is None:
            return
        assert isinstance(dir_raw, pathlib.Path)
        filename = pathlib.Path(self.filename)
        filenamebak = dir_raw / f"{filename.name}.bak"
        filenamebak.write_text(filename.read_text())

    @property
    def configsteps(self) -> Iterable[ConfigStep]:
        yield self.step_0_settle
        yield self.step_1_fast
        yield self.step_2_medium
        yield self.step_3_slow

    def measure(self, dir_measurement, dir_raw, do_exit=True):
        assert isinstance(dir_measurement, pathlib.Path)
        assert isinstance(dir_raw, pathlib.Path)

        try:
            self.measure_for_all_steps(dir_measurement=dir_measurement, dir_raw=dir_raw)
            if do_exit:
                ExitCode.OK.os_exit()
        except Exception as e:  # pylint: disable=broad-except
            import traceback

            traceback.print_exc()
            ExitCode.ERROR_PICOSCOPE.os_exit(msg=str(e))

    def measure_for_all_steps(
        self, dir_measurement: pathlib.Path, dir_raw: pathlib.Path
    ):
        assert isinstance(dir_measurement, pathlib.Path)
        assert isinstance(dir_raw, pathlib.Path)

        _lock = FilelockMeasurement()

        for configstep in self.configsteps:
            if configstep.skip:
                continue
            if self.capture_raw_hit_anykey:
                input("capture_raw_hit_anykey=True: Hit <enter> to start acquistion...")
            filename_capture_raw = configstep.get_filename_capture_raw(
                config_setup=self, dir_raw=dir_raw
            )
            # if not filename_capture_raw.is_file():
            #     logger.info(f"{filename_capture_raw}: does not exist: No processing!")
            #     continue
            logger.info(f"{filename_capture_raw}: processing...")

            _lock.update_status(f"Measuring: {dir_raw.name} / {configstep.stepname}")
            ad_low_noise_float_2023 = self.module_instrument.Instrument(configstep)
            from . import (
                program_config_instrument_ad_low_noise_float_2023,
                program_instrument_ad_low_noise_float_2023,
            )

            if isinstance(
                configstep,
                program_config_instrument_ad_low_noise_float_2023.ConfigStepAdLowNoiseFloat2023,
            ):
                if isinstance(
                    ad_low_noise_float_2023,
                    program_instrument_ad_low_noise_float_2023.Instrument,
                ):
                    # Call connect to aquire the jumper settings from the hardware
                    ad_low_noise_float_2023.connect(PcbParams())
                    gain_from_jumpers = (
                        ad_low_noise_float_2023.adc.pcb_status.gain_from_jumpers
                    )
                    configstep.input_internal_Vp = AD_FS_V / gain_from_jumpers
                else:
                    configstep.input_internal_Vp = 42.0

            configstep.dump(logger=logger, indent="")
            process_config = configstep.process_config
            process_config.validate()
            sample_process = program_fir.SamplingProcess(process_config, dir_raw)
            ad_low_noise_float_2023.acquire(
                configstep=configstep,
                stream_output=sample_process.output,
                filename_capture_raw=filename_capture_raw,
                filelock_measurement=_lock,
            )
            ad_low_noise_float_2023.close()

            if _lock.requested_stop_soft():
                return
