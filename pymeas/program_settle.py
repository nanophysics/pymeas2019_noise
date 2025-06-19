import logging
import pathlib

import numpy as np

from . import library_filelock, program_configsetup, program_fir
from .library_filelock import ExitCode

logger = logging.getLogger("logger")


class Settle:  # pylint: disable=too-many-instance-attributes
    """
    Stream-Sink: Implements a Stream-Interface
    Stream-Source: Drives a output of Stream-Interface
    """

    def __init__(self, config, directory):
        assert isinstance(directory, pathlib.Path)
        assert isinstance(config, program_configsetup.SamplingProcessConfig)

        if config.settle:
            if config.settle_time_ok_s + 1.0 > config.duration_s:
                raise Exception(f"Will never settle if settle_time_ok_s {config.settle_time_ok_s:0.1}s is bigger than duration_s {config.duration_s:0.1}s!")

        self.__config = config
        self.__dt_s = None

        self.__input_range_V = self.__config.input_Vp * self.__config.skalierungsfaktor
        self.__ok_range_V = self.__input_range_V * self.__config.settle_input_part
        self.__fifo = np.empty(0, dtype=program_fir.NUMPY_FLOAT_TYPE)
        self.__last_sample_outside_s = 0.0
        self.__filelock_measurement = library_filelock.FilelockMeasurement()

    def init(self, stage, dt_s):
        self.__dt_s = dt_s

    def done(self):
        ExitCode.ERROR_INPUT_NOT_SETTLE.os_exit(msg="Settling: The input voltage did not settle!")

    def push(self, array_in):
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        if array_in is None:
            return None
        assert isinstance(array_in, np.ndarray)

        self.__fifo = np.append(self.__fifo, array_in)

        now_s = self.__dt_s * len(self.__fifo)

        if (array_in.max() > self.__ok_range_V) or (array_in.min() < -self.__ok_range_V):
            # A sample is outside the range
            self.__last_sample_outside_s = now_s

        if self.__filelock_measurement.requested_skip_settle():
            logger.info("Settle: DONE (Manually skipped settling)")
            raise StopIteration("Manually skipped settling")

        if self.__filelock_measurement.requested_stop_soft():
            logger.error("Aborted by ctrl-C")
            logger.error("Exiting!")
            ExitCode.CTRL_C.os_exit()

        time_left_s = self.__config.settle_time_ok_s + self.__last_sample_outside_s - now_s

        now_V = float(array_in[-1])
        status = f"Settle: inputRange +-{self.__input_range_V:0.2e}V, ok_range +-{self.__ok_range_V:0.2e}V, now {now_V:0.2e}V, wait for ok {self.__config.settle_time_ok_s:0.1f}s, {time_left_s:0.0f}s left"
        self.__filelock_measurement.update_status(status)

        if time_left_s < 0:
            logger.info("Settle: DONE")
            raise StopIteration("Successfully settled")

        return None
