import enum
import types
import logging
import pathlib
from typing import Iterable, Optional

from .program_lockingmixin import LockingMixin
from .library_filelock import ExitCode, FilelockMeasurement

from . import program_fir

logger = logging.getLogger("logger")


class SamplingProcessConfig(
    LockingMixin
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        self.fir_count: int = 0
        self.fir_count_skipped: int = 0
        self.stepname: str = LockingMixin.TO_BE_SET
        self.settle: bool = False
        self.settle_time_ok_s: float = None
        self.settle_input_part: float = None
        self.skalierungsfaktor: float = 1.0
        self.input_Vp: float = 1.0
        self.duration_s: float = LockingMixin.TO_BE_SET

        self._lock()

    def validate(self):
        assert isinstance(self.fir_count, int)
        assert isinstance(self.fir_count_skipped, int)
        assert isinstance(self.stepname, str)
        assert isinstance(self.settle, bool)
        assert isinstance(self.settle_time_ok_s, (type(None), float))
        assert isinstance(self.settle_input_part, (type(None), float))
        if self.settle:
            assert isinstance(self.settle_time_ok_s, float)
            assert isinstance(self.settle_input_part, float)
        assert isinstance(self.skalierungsfaktor, float)
        assert isinstance(self.input_Vp, float)
        assert isinstance(self.duration_s, float)

        self._freeze()


class ConfigStep(
    LockingMixin
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        self.stepname: str = LockingMixin.TO_BE_SET
        self.settle: bool = False
        self.settle_time_ok_s: float = None
        self.settle_input_part: float = None
        self.skalierungsfaktor: float = LockingMixin.TO_BE_SET
        self.fir_count: int = 0
        self.fir_count_skipped: int = 0
        self.input_channel: str = LockingMixin.TO_BE_SET
        self.input_Vp: enum.Enum = LockingMixin.TO_BE_SET
        self.bandwidth: str = LockingMixin.TO_BE_SET
        self.offset: float = LockingMixin.TO_BE_SET
        self.resolution: str = LockingMixin.TO_BE_SET
        self.duration_s: float = LockingMixin.TO_BE_SET
        self.dt_s: float = LockingMixin.TO_BE_SET
        self.skip: bool = False

        self._lock()

    def validate(self):
        assert isinstance(self.stepname, str)
        assert isinstance(self.settle, bool)
        assert isinstance(self.settle_time_ok_s, (type(None), float))
        assert isinstance(self.settle_input_part, (type(None), float))
        if self.settle:
            assert isinstance(self.settle_time_ok_s, float)
            assert isinstance(self.settle_input_part, float)
        assert isinstance(self.skalierungsfaktor, float)
        assert isinstance(self.fir_count, int)
        assert isinstance(self.fir_count_skipped, int)
        assert isinstance(self.input_channel, str)
        assert isinstance(self.input_Vp, enum.Enum)
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
        c.input_Vp = self.input_Vp.V  # pylint: disable=no-member
        c.duration_s = self.duration_s
        return c

    def get_filename_capture_raw(
        self, config_setup: "ConfigSetup", dir_raw: pathlib.Path
    ) -> Optional[pathlib.Path]:
        if config_setup.capture_raw:
            return dir_raw / f"capture_raw_{self.stepname}.raw"
        return None


class InputRangeKeysight34401A(enum.Enum):
    RANGE_100mV = "0.1"
    RANGE_1V = "1"
    RANGE_10V = "10"
    RANGE_100V = "100"
    RANGE_1000V = "1000"

    @property
    def V(self) -> float:
        return {
            InputRangeKeysight34401A.RANGE_100mV: 0.1,
            InputRangeKeysight34401A.RANGE_1V: 1.0,
            InputRangeKeysight34401A.RANGE_10V: 10.0,
            InputRangeKeysight34401A.RANGE_100V: 100.0,
            InputRangeKeysight34401A.RANGE_1000V: 1000.0,
        }[self]


class ConfigStepKeysight34401A(
    ConfigStep
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        super().__init__()
        self.input_channel: str = "42"
        self.input_Vp: enum.Enum = InputRangeKeysight34401A.RANGE_100V
        self.bandwidth: str = "42"
        self.offset: float = 42.0
        self.resolution: str = "42"


class ConfigStepKeithley6517A(
    ConfigStep
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        super().__init__()
        self.input_channel: str = "42"
        self.input_Vp: enum.Enum = InputRangeKeysight34401A.RANGE_100V
        self.bandwidth: str = "42"
        self.offset: float = 42.0
        self.resolution: str = "42"


class ConfigStepSkip(
    ConfigStep
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    def __init__(self):
        super().__init__()
        self.skalierungsfaktor: float = 42.0
        self.input_channel: str = "42"
        self.input_Vp: enum.Enum = InputRangeKeysight34401A.RANGE_100V
        self.bandwidth: str = "42"
        self.offset: float = 42.0
        self.resolution: str = "42"
        self.duration_s: float = 42.0
        self.dt_s: float = 42.0
        self.skip: bool = True


class ConfigSetup(LockingMixin):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.filename: str = None
        self.setup_name: str = LockingMixin.TO_BE_SET
        self.module_instrument: types.ModuleType = LockingMixin.TO_BE_SET
        self.capture_raw: bool = False
        "Save the datastream from the scope directly to a file and do not process it."
        self.capture_raw_hit_anykey: bool = False
        self.step_0_settle: ConfigStep = LockingMixin.TO_BE_SET
        self.step_1_fast: ConfigStep = LockingMixin.TO_BE_SET
        self.step_2_medium: ConfigStep = LockingMixin.TO_BE_SET
        self.step_3_slow: ConfigStep = LockingMixin.TO_BE_SET

        self._lock()

    def validate(self):
        assert isinstance(self.filename, (type(None), str))
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
            ad_low_noise_float_2023 = self.module_instrument.Instrument(
                configstep
            )  # pylint: disable=no-member
            ad_low_noise_float_2023.connect()
            sample_process = program_fir.SamplingProcess(
                configstep.process_config, dir_raw
            )
            ad_low_noise_float_2023.acquire(
                configstep=configstep,
                stream_output=sample_process.output,
                filename_capture_raw=filename_capture_raw,
                filelock_measurement=_lock,
            )
            ad_low_noise_float_2023.close()

            if _lock.requested_stop_soft():
                return


class ConfigSetupKeysight34401A(ConfigSetup):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        step = ConfigStepSkip()
        step.stepname = "0_settle"
        self.step_0_settle = step

        step = ConfigStepSkip()
        step.stepname = "1_fast"
        self.step_1_fast = step

        step = ConfigStepSkip()
        step.stepname = "2_medium"
        self.step_2_medium = step

    @property
    def configsteps(self):
        yield self.step_3_slow
