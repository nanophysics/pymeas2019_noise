import logging
import pathlib

import numpy as np

from . import program_configsetup, program_fir, library_filelock

logger = logging.getLogger("logger")


class Instrument:
    def __init__(self, configstep):
        pass

    def connect(self):
        pass

    def close(self):
        pass

    def acquire(
        self,
        configstep: program_configsetup.ConfigStep,
        filename_capture_raw: pathlib.Path | None,
        stream_output: program_fir.UniformPieces,
        filelock_measurement: library_filelock.FilelockMeasurement,
    ):  # pylint: disable=too-many-statements
        assert isinstance(configstep, program_configsetup.ConfigStep)
        assert isinstance(filename_capture_raw, pathlib.Path | None)
        assert isinstance(stream_output, program_fir.UniformPieces)
        assert isinstance(filelock_measurement, library_filelock.FilelockMeasurement)

        pushcalulator_next = program_fir.PushCalculator(configstep.dt_s)
        stream_output.init(stage=0, dt_s=configstep.dt_s)
        push_size_samples = pushcalulator_next.push_size_samples

        def flush_stages():
            max_calculations = 30
            for _ in range(max_calculations):
                calculation_stage = stream_output.push(None)
                done = len(calculation_stage) == 0
                if done:
                    break

        if filename_capture_raw is None:
            return

        with filename_capture_raw.open("rb") as f:
            while True:
                push_size_bytes = 4 * push_size_samples
                buffer = f.read(push_size_bytes)
                if len(buffer) < push_size_bytes:
                    flush_stages()
                    return

                array = np.frombuffer(buffer, dtype=np.float32)
                assert len(array) == push_size_samples
                stream_output.push(array)

                flush_stages()
