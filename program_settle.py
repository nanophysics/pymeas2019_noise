import sys
import pathlib
import logging

import numpy as np

import library_filelock
import program_fir


logger = logging.getLogger("logger")


INPUT_PART = 0.5  # part of the input range.
TIME_OK_S = 100.0


class Settle:  # pylint: disable=too-many-instance-attributes
    """
    Stream-Sink: Implements a Stream-Interface
    Stream-Source: Drives a output of Stream-Interface
    """
    def __init__(self, config, directory):
        assert isinstance(directory, pathlib.Path)

        self.__config = config
        self.__directory = directory
        self.__dt_s = None

        self.__input_range_V = self.__config.input_Vp * self.__config.skalierungsfaktor
        self.__ok_range_V = self.__input_range_V * INPUT_PART
        self.__fifo = np.empty(0, dtype=program_fir.NUMPY_FLOAT_TYPE)
        self.__last_sample_outside_s = 0.0
        self.__filelock_measurement = library_filelock.FilelockMeasurement()

    def init(self, stage, dt_s):
        self.__dt_s = dt_s

    def done(self):
        logger.error(f"Settling: The input voltage did not settle!")
        sys.exit(42)

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

        self.__fifo = np.append(self.__fifo, array_in)

        now_s = self.__dt_s * len(self.__fifo)

        if (array_in.max() > self.__ok_range_V) or (array_in.min() < -self.__ok_range_V):
            # A sample is outside the range
            self.__last_sample_outside_s = now_s

        if self.__filelock_measurement.requested_stop_soft():
            logger.error("Aborted by ctrl-C")
            sys.exit(0)

        time_left_s = TIME_OK_S + self.__last_sample_outside_s - now_s

        now_V = float(array_in[-1]) / self.__config.skalierungsfaktor
        status = f"Settle: inputRange +-{self.__input_range_V:0.2e}V, ok_range +-{self.__ok_range_V:0.2e}V, now {now_V:0.2e}V, wait for ok {TIME_OK_S}s, {time_left_s:0.0f}s left"
        self.__filelock_measurement.update_status(status)

        if time_left_s < 0:
            logger.info("Settle: DONE")
            raise StopIteration("Successfully settled")

        return None
