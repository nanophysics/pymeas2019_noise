import sys
import math
import pathlib
import logging

import numpy as np
import scipy.signal

from . import program_classify
from . import program_settle
from . import program_fir_plot
from . import program_fir_multiprocess
from . import program_configsetup

logger = logging.getLogger("logger")

DEBUG_FIFO = False

SAMPLES_DENSITY = 2 ** 12  # length of periodogram (2**12=4096)
# PERIODOGRAM_OVERLAP = 2 ** 5  # number of overlaps (2**5=32)
PERIODOGRAM_OVERLAP = 2 ** 4  # number of overlaps (2**4=16)
assert SAMPLES_DENSITY % PERIODOGRAM_OVERLAP == 0
SAMPLES_SELECT_MAX = 2 ** 23  # (2**23=8388608)


# NUMPY_FLOAT_TYPE=np.float
NUMPY_FLOAT_TYPE = np.float32

classify_stepsize = program_classify.Classify()

#   <---------------- INPUT ---------========------->
#
#  |<-- LEFT -->|<--====- SELECT -====-->|<- RIGHT ->|
#                   |<- DECIMATE ->|
DECIMATE_FACTOR = 2
SAMPLES_LEFT = 100  # 36
SAMPLES_RIGHT = 100  # 36
SAMPLES_LEFT_RIGHT = SAMPLES_LEFT + SAMPLES_RIGHT
assert SAMPLES_LEFT % DECIMATE_FACTOR == 0
assert SAMPLES_RIGHT % DECIMATE_FACTOR == 0


class PushCalculator:
    """
    >>> [PushCalculator(dt_s).push_size_samples for dt_s in (1.0/125e6, 1.0/1953125.0, 1.0)]
    [4194304, 1048576, 256]
    """

    def __init__(self, dt_s):
        self.dt_s = dt_s
        self.push_size_samples = self.__calculate_push_size_samples()
        self.previous_fir_samples_select = self.push_size_samples * DECIMATE_FACTOR
        self.previous_fir_samples_input = self.previous_fir_samples_select + SAMPLES_LEFT_RIGHT

    def __calculate_push_size_samples(self):
        # 0.536870912s push_size_sample=1048576
        # ...
        # 0.536870912s push_size_sample=8192
        # 0.536870912s push_size_sample=4096
        # 0.536870912s push_size_sample=2048
        # 0.536870912s push_size_sample=1024
        # 0.536870912s push_size_sample=512
        # 0.536870912s push_size_sample=256
        # 0.536870912s push_size_sample=128
        # ...
        # 17.179869184s push_size_sample=128
        push_size = 1.0 / self.dt_s / 1953125 * 2097152 / 2.0
        push_size = 2**round(math.log2(push_size + 0.5))
        push_size = max(push_size, SAMPLES_DENSITY // PERIODOGRAM_OVERLAP)
        push_size = min(push_size, SAMPLES_SELECT_MAX // 2)
        return push_size


class FIR:  # pylint: disable=too-many-instance-attributes
    """
    Stream-Sink: Implements a Stream-Interface
    Stream-Source: Drives a output of Stream-Interface
    """

    def __init__(self, out):
        self.out = out
        self.prev = None
        self.array = None
        self.statistics_count = None
        self.statistics_samples_out = None
        self.statistics_samples_in = None
        self.stage = None
        self.__dt_s = None
        self.pushcalulator_next = None

    def init(self, stage, dt_s, prev):
        self.prev = prev
        self.statistics_count = 0
        self.statistics_samples_out = 0
        self.statistics_samples_in = 0
        self.stage = stage
        self.__dt_s = dt_s
        decimated_dt_s = dt_s * DECIMATE_FACTOR
        self.pushcalulator_next = PushCalculator(decimated_dt_s)
        logger.debug(f"stage {self.stage} push_size_samples {self.pushcalulator_next.push_size_samples} time_s {self.pushcalulator_next.dt_s*self.pushcalulator_next.push_size_samples}")
        self.out.init(stage=stage + 1, dt_s=decimated_dt_s, prev=self)

    def done(self):
        logger.debug(f"Statistics {self.stage}: count {self.statistics_count}, samples in {self.statistics_samples_in*self.__dt_s:0.3f}s, samples out {self.statistics_samples_out*self.__dt_s*DECIMATE_FACTOR:0.3f}s")
        self.out.done()

    def print_size(self, f):
        array_len = -1 if self.array is None else len(self.array)
        print(f"stage {self.stage} FIR: array_len: {array_len}")

        self.out.print_size(f)

    def push(self, array_in):  # pylint: disable=too-many-return-statements
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        assert array_in is not None

        def array_in_is_none():
            if self.array is None:
                # Nothing to decimate
                return

            if len(self.array) < self.pushcalulator_next.previous_fir_samples_input:
                # Not sufficient data
                return

            array_decimate = self.decimate(self.array[: self.pushcalulator_next.previous_fir_samples_input])
            assert len(array_decimate) == self.pushcalulator_next.push_size_samples
            self.statistics_samples_out += len(array_decimate)
            self.out.push(array_decimate)
            # Save the remainting part to 'self.array'
            self.array = self.array[self.pushcalulator_next.previous_fir_samples_select :]
            assert len(self.array) >= SAMPLES_LEFT_RIGHT

        assert len(array_in) % self.pushcalulator_next.push_size_samples == 0

        if self.array is None:
            # The first time. Left&Right must be faked.
            self.array = np.flip(array_in[:SAMPLES_LEFT_RIGHT])

        self.statistics_samples_in += len(array_in)
        # Add to 'self.array'
        self.array = np.append(self.array, array_in)

        if DEBUG_FIFO:
            if self.__dt_s >= 0.01:
                logger.debug(f"stage {self.stage} decimate received push {len(array_in)} samples, total {len(self.array)} samples")

        array_in_is_none()

    def decimate(self, array_decimate):
        self.statistics_count += 1

        if DEBUG_FIFO:
            array_len = -1 if self.array is None else len(self.array)
            logger.debug(f"decimate, stage {self.stage}, array_len: {array_len}")
        assert len(array_decimate) > SAMPLES_LEFT_RIGHT
        assert len(array_decimate) % DECIMATE_FACTOR == 0

        CORRECTION_FACTOR = 1.01  # Peter: estimated from measurements with synthetic data, the decimate seams to be a bit off, quick and dirty
        array_decimated = CORRECTION_FACTOR * scipy.signal.decimate(array_decimate, DECIMATE_FACTOR, ftype="iir", zero_phase=True)

        assert len(array_decimated) == len(array_decimate) // DECIMATE_FACTOR
        index_from = SAMPLES_LEFT // DECIMATE_FACTOR
        index_to = len(array_decimated) - SAMPLES_RIGHT // DECIMATE_FACTOR
        array_decimated = array_decimated[index_from:index_to]
        return array_decimated


class Density:  # pylint: disable=too-many-instance-attributes
    """
    Stream-Sink: Implements a Stream-Interface
    Stream-Source: Drives a output of Stream-Interface

    This class processes the data-stream and every `self.config.interval_s` does some density calculation...
    The class LsdSummary will the access self.Pxx_sum/self.Pxx_n to create a density plot.
    """

    def __init__(self, out, config, directory):
        assert isinstance(directory, pathlib.Path)

        self.out = out
        self.prev = None
        self.__config = config
        self.__directory = directory
        self.__stepsize_bins = classify_stepsize.bins_factory()

        self.frequencies = None
        self.__Pxx_sum = np.zeros(SAMPLES_DENSITY // 2 + 1, dtype=np.float64)
        # self.__Pxx_sum = np.zeros(SAMPLES_DENSITY // 2 + 1, dtype=np.float32)
        self.__Pxx_n = 0
        self.__stage = None
        self.__dt_s = None
        self.__pushcalulator = None
        self.__mode_fifo = None
        self.__fifo = None
        self.__fifo_size_s = None

    def print_size(self, f):
        common = f"stage {self.__stage} Density: Pxx_n: {self.__Pxx_n}"
        if self.__mode_fifo:
            fifo_len = len(self.__fifo)
            print(f"{common}, fifo_len: {fifo_len}, {fifo_len*self.__dt_s:0.2e}s")
        else:
            push_size_samples = self.__pushcalulator.push_size_samples
            print(f"{common}, push_size_samples: {push_size_samples}, {push_size_samples*self.__dt_s:0.2e}s")

        self.out.print_size(f)

    def init(self, stage, dt_s, prev):
        self.prev = prev
        self.__stage = stage
        self.__dt_s = dt_s
        self.__pushcalulator = PushCalculator(dt_s)
        self.__mode_fifo = self.__pushcalulator.push_size_samples < SAMPLES_DENSITY
        if self.__mode_fifo:
            # In this stage, only a few samples will be pushed
            # We create a fifo
            self.__fifo = np.empty(0, dtype=NUMPY_FLOAT_TYPE)
        else:
            # In this stage, we will get sufficient samples for every push
            # There is no need to allocate a fifo-array.
            self.__fifo = None

            self.__fifo_size_s = SAMPLES_DENSITY * self.__dt_s

        self.out.init(stage=stage, dt_s=dt_s, prev=self)

    def done(self):
        self.out.done()

    @property
    def fifo_size_s(self) -> float:
        if self.__fifo_size_s:
            return self.__fifo_size_s
        return len(self.__fifo) * self.__dt_s

    def calculate_samples_flipped(self):
        # We flip samples to be able to decimate. These samples are not real measured samples.
        # Therefore we remove them for the density calculation. This only happens in the beginning.
        # stage samples
        #    0     0
        #    1    50
        #    2    75
        #  100   100
        samples = round(SAMPLES_LEFT - SAMPLES_LEFT / (DECIMATE_FACTOR ** self.__stage))
        assert samples <= SAMPLES_LEFT
        return samples

    def do_preview(self):
        # TODO: How to self.prev.prev ?
        return

        if not self.__mode_fifo:
            return False
        if self.__Pxx_n > 0:
            # Preview should not overwrite real data.
            return False

        try:
            prev_density = self.prev.prev
        except AttributeError:
            # There is not previous stage!
            # This is happens with a very slow instrument: We are the first stage
            return True

        if self.fifo_size_s < prev_density.fifo_size_s * 1.01:
            return False
        logger.debug(f"Preview {self.__stage} {self.fifo_size_s}s > {prev_density.fifo_size_s}s")
        return True

    def push(self, array_in):
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        assert array_in is not None

        def array_in_is_none():
            if self.__fifo is None:
                return

            if len(self.__fifo) < SAMPLES_DENSITY:
                return

            # Time is over. Calculate density
            self.density(self.__fifo)
            if self.__mode_fifo:
                len_before = len(self.__fifo)
                self.__fifo = self.__fifo[self.__pushcalulator.push_size_samples :]
                if DEBUG_FIFO:
                    logger.debug(f"stage {self.__stage} density squash fifo from  {len_before} to {len(self.__fifo)} samples")
                return
            self.__fifo = None

        self.out.push(array_in)

        # Add to 'self.array'
        if self.__mode_fifo:
            assert len(array_in) == self.__pushcalulator.push_size_samples
            array_tmp = array_in
            if len(self.__fifo) == 0:
                # The very first time: Remove SAMPLES_LEFT
                samples_flipped = self.calculate_samples_flipped()
                assert samples_flipped < len(array_in)
                array_tmp = array_in[samples_flipped:]
            self.__fifo = np.append(self.__fifo, array_tmp)

            if DEBUG_FIFO:
                if self.__dt_s >= 0.01:
                    logger.debug(f"stage {self.__stage} density received push {len(array_in)} samples, total {len(self.__fifo)} samples")

            if self.do_preview():
                self.density_preview(self.__fifo)

            array_in_is_none()
            return

        assert len(array_in) >= SAMPLES_DENSITY
        self.__fifo = array_in[:SAMPLES_DENSITY]
        # logger.debug(f"Density Stage {self.__stage:02d} dt_s {self.__dt_s:016.12f}, len(array_in)={len(array_in)}")

        array_in_is_none()

    def density(self, array):
        # logger.debug(f"Density Stage {self.__stage:02d} dt_s {self.__dt_s:016.12f}, len(array)={len(array)} calculation")

        self.frequencies, Pxx = scipy.signal.periodogram(array[:SAMPLES_DENSITY], 1 / self.__dt_s, window="hamming", detrend="linear")  # Hz, V^2/Hz

        # Averaging
        assert len(self.__Pxx_sum) == len(Pxx)
        if self.__Pxx_n == 0:
            if self.__Pxx_sum.dtype != Pxx.dtype:
                # logger.warning(f"Stage {self.__stage}: Expected {Pxx.dtype} but got {self.__Pxx_sum.dtype}.")
                pass
        self.__Pxx_sum += Pxx
        self.__Pxx_n += 1
        # Stepsize statistics
        stepsizes_V = np.abs(np.diff(array))
        for stepsize_V in stepsizes_V:
            self.__stepsize_bins.add(stepsize_V)

        bins_total_count = np.sum(self.__stepsize_bins.count)
        stepsize_bins_count = self.__stepsize_bins.count / (self.__dt_s * bins_total_count)

        _filenameFull = program_fir_plot.DensityPlot.save(config=self.__config, directory=self.__directory, stage=self.__stage, dt_s=self.__dt_s, frequencies=self.frequencies, Pxx_n=self.__Pxx_n, Pxx_sum=self.__Pxx_sum, stepsize_bins_count=stepsize_bins_count, stepsize_bins_V=self.__stepsize_bins.V, samples_V=array)

    def density_preview(self, array):
        self.frequencies, Pxx = scipy.signal.periodogram(array, 1 / self.__dt_s, window="hamming", detrend="linear")  # Hz, V^2/Hz

        _filenameFull = program_fir_plot.DensityPlot.save(config=self.__config, directory=self.__directory, stage=self.__stage, dt_s=self.__dt_s, frequencies=self.frequencies, Pxx_n=1, Pxx_sum=Pxx, stepsize_bins_count=self.__stepsize_bins.count, stepsize_bins_V=self.__stepsize_bins.V, samples_V=array)


class OutTrash:
    """
    Stream-Sink: Implements a Stream-Interface
    """

    def __init__(self):
        self.prev = None
        self.stage = None
        self.dt_s = None
        self.array = np.empty(0, dtype=NUMPY_FLOAT_TYPE)

    def init(self, stage, dt_s, prev):
        self.prev = prev
        self.stage = stage
        self.dt_s = dt_s

    def done(self):
        pass

    def print_size(self, f):
        pass

    def push(self, array_in):
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        assert array_in is not None

class InSynthetic:
    """
    Stream-Source: Drives a output of Stream-Interface
    """

    def __init__(self, out, dt_s, time_total_s, signal):
        self.out = out
        self.dt_s = dt_s
        self.total_samples = time_total_s / dt_s
        self.signal = signal
        self.pushcalulator_next = PushCalculator(dt_s)
        self.out.init(stage=0, dt_s=dt_s)

    def process(self):
        push_size_samples = self.pushcalulator_next.push_size_samples
        sample_start = 0

        while sample_start < self.total_samples:
            array = self.signal.calculate(dt_s=self.dt_s, sample_start=sample_start, push_size_samples=push_size_samples)
            assert len(array) == push_size_samples
            self.out.push(array)
            sample_start += push_size_samples

            print("----------------")
            self.out.print_size(sys.stdout)
            print("----------------")

class UniformPieces:
    """
    Stream-Sink: Implements a Stream-Interface
    Stream-Source: Drives a output of Stream-Interface
    Sends arrays of defined size.
    """

    def __init__(self, out):
        self.out = out
        self.array = np.empty(0, dtype=NUMPY_FLOAT_TYPE)
        self.stage = None
        self.total_samples = None
        self.pushcalulator_next = None
        self._calculation_not_finished_counter = 0

    def init(self, stage, dt_s):
        self.stage = stage
        self.total_samples = 0
        self.out.init(stage=stage, dt_s=dt_s, prev=None)
        self.pushcalulator_next = PushCalculator(dt_s)

    def done(self):
        self.out.done()

    def print_size(self, f):
        self.out.print_size(f)

    def push(self, array_in):
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        assert array_in is not None

        self.total_samples += len(array_in)
        self.array = np.append(self.array, array_in)

        push_size_samples = self.pushcalulator_next.push_size_samples
        if len(self.array) >= push_size_samples:
            self.out.push(self.array[:push_size_samples])
            # Save the remainting part to 'self.array'
            self.array = self.array[push_size_samples:]


class SamplingProcess:
    def __init__(self, config, directory_raw):
        assert isinstance(config, program_configsetup.SamplingProcessConfig)
        assert isinstance(directory_raw, pathlib.Path)

        self.config = config
        self.directory_raw = directory_raw

        directory_raw.mkdir(parents=True, exist_ok=True)

        if config.settle:
            self.output = program_settle.Settle(config=config, directory=self.directory_raw)
            return

        o = OutTrash()

        for _i in range(config.fir_count - 1):
            o = Density(o, config=config, directory=self.directory_raw)
            o = program_fir_multiprocess.InterprocessQueue(o)
            o = FIR(o)

        o = Density(o, config=config, directory=self.directory_raw)
        o = UniformPieces(o)
        self.output = o


if __name__ == "__main__":
    import doctest

    doctest.testmod()
