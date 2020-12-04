import sys
import enum
import types
import logging
import pathlib

from .program_lockingmixin import LockingMixin

from . import library_filelock
from . import program_fir

logger = logging.getLogger("logger")


class SamplingProcessConfig(LockingMixin):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
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


class ConfigStep(LockingMixin):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
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
        self.bandwitdth: str = LockingMixin.TO_BE_SET
        self.offset: float = LockingMixin.TO_BE_SET
        self.resolution: str = LockingMixin.TO_BE_SET
        self.duration_s: float = LockingMixin.TO_BE_SET
        self.dt_s: float = LockingMixin.TO_BE_SET

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
        assert isinstance(self.bandwitdth, str)
        assert isinstance(self.offset, float)
        assert isinstance(self.resolution, str)
        assert isinstance(self.duration_s, float)
        assert isinstance(self.dt_s, float)

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


class ConfigSetup(LockingMixin):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.setup_name: str = LockingMixin.TO_BE_SET
        self.module_instrument: types.ModuleType = LockingMixin.TO_BE_SET
        self.configsteps: list = LockingMixin.TO_BE_SET

        self._lock()

    def validate(self):
        assert isinstance(self.setup_name, str)
        assert isinstance(self.module_instrument, types.ModuleType)
        assert isinstance(self.configsteps, list)

        self._freeze()

        for configstep in self.configsteps:
            configstep.validate()

    def measure(self, dir_measurement, dir_raw):
        assert isinstance(dir_measurement, pathlib.Path)
        assert isinstance(dir_raw, pathlib.Path)

        try:
            self.measure_for_all_steps(dir_measurement=dir_measurement, dir_raw=dir_raw)
        except Exception:  # pylint: disable=broad-except
            import traceback

            traceback.print_exc()
            logger.info("Hit any key to terminate")
            sys.stdin.read()

    def measure_for_all_steps(self, dir_measurement, dir_raw):
        assert isinstance(dir_measurement, pathlib.Path)
        assert isinstance(dir_raw, pathlib.Path)

        _lock = library_filelock.FilelockMeasurement()

        for configstep in self.configsteps:
            _lock.update_status(f"Measuring: {dir_raw.name} / {configstep.stepname}")
            picoscope = self.module_instrument.Instrument(configstep)  # pylint: disable=no-member
            picoscope.connect()
            sample_process = program_fir.SamplingProcess(configstep.process_config, dir_raw)
            picoscope.acquire(configstep=configstep, stream_output=sample_process.output, filelock_measurement=_lock)
            picoscope.close()

            if _lock.requested_stop_soft():
                return
