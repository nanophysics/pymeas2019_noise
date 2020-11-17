import pathlib
import logging

import numpy as np
import scipy.signal
import program_classify
import program_fir_plot

logger = logging.getLogger("logger")

TIME_INTERVAL_S = 0.9
SAMPLES_DENSITY = 2 ** 12  # lenght of periodogram
PERIODOGRAM_OVERLAP = 2 ** 4  # number of overlaps
assert SAMPLES_DENSITY % PERIODOGRAM_OVERLAP == 0
SAMPLES_SELECT_MAX = 2 ** 23

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
        self.push_size_samples = self.__calulcate_push_size_samples()
        self.previous_fir_samples_select = self.push_size_samples * DECIMATE_FACTOR
        self.previous_fir_samples_input = self.previous_fir_samples_select + SAMPLES_LEFT_RIGHT

    def __calulcate_push_size_samples(self):
        push_size = 1.0 / self.dt_s / 1953125 * 2097152 / 2.0
        push_size = int(push_size + 0.5)
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
        self.array = None
        self.fake_left_right = True
        self.statistics_count = None
        self.statistics_samples_out = None
        self.statistics_samples_in = None
        self.stage = None
        self.__dt_s = None
        self.TAG_PUSH = None
        self.pushcalulator_next = None

    def init(self, stage, dt_s):
        self.statistics_count = 0
        self.statistics_samples_out = 0
        self.statistics_samples_in = 0
        self.stage = stage
        self.__dt_s = dt_s
        self.TAG_PUSH = f"FIR {self.stage}"
        decimated_dt_s = dt_s * DECIMATE_FACTOR
        self.pushcalulator_next = PushCalculator(decimated_dt_s)
        logger.debug(f"stage {self.stage} push_size_samples {self.pushcalulator_next.push_size_samples} time_s {self.pushcalulator_next.dt_s*self.pushcalulator_next.push_size_samples}")
        self.out.init(stage=stage + 1, dt_s=decimated_dt_s)

    def done(self):
        logger.debug(f"Statistics {self.stage}: count {self.statistics_count}, samples in {self.statistics_samples_in*self.__dt_s:0.3f}s, samples out {self.statistics_samples_out*self.__dt_s*DECIMATE_FACTOR:0.3f}s")
        self.out.done()

    def push(self, array_in):  # pylint: disable=too-many-return-statements
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        if not self.fake_left_right:
            if self.array is None:
                if array_in is None:
                    return self.out.push(None)
                # This is the veriy first time
                # Keep the oldest SAMPLES_LEFT_RIGHT
                assert len(array_in) >= SAMPLES_LEFT_RIGHT
                self.array = array_in[-SAMPLES_LEFT_RIGHT:]
                self.statistics_samples_in += len(array_in)
                return self.out.push(None)

        if array_in is None:
            if self.array is None:
                return self.out.push(None)
            # array_in is None: We may decimate
            if len(self.array) < self.pushcalulator_next.previous_fir_samples_input:
                # Not sufficient data
                # Give the next stage a chance to decimate!
                return self.out.push(None)

            array_decimate = self.decimate(self.array[: self.pushcalulator_next.previous_fir_samples_input])
            assert len(array_decimate) == self.pushcalulator_next.push_size_samples
            self.statistics_samples_out += len(array_decimate)
            self.out.push(array_decimate)
            # Save the remainting part to 'self.array'
            self.array = self.array[self.pushcalulator_next.previous_fir_samples_select :]
            assert len(self.array) >= SAMPLES_LEFT_RIGHT
            return self.TAG_PUSH

        assert len(array_in) % self.pushcalulator_next.push_size_samples == 0

        if self.fake_left_right:
            if self.array is None:
                # The first time. Left&Right must be faked.
                self.array = np.flip(array_in[:SAMPLES_LEFT_RIGHT])
                return None

        self.statistics_samples_in += len(array_in)
        # Add to 'self.array'
        self.array = np.append(self.array, array_in)
        return None

    def decimate(self, array_decimate):
        self.statistics_count += 1

        logger.debug(f"{self.stage},")
        assert len(array_decimate) > SAMPLES_LEFT_RIGHT
        assert len(array_decimate) % DECIMATE_FACTOR == 0

        CORRECTION_FACTOR = 1.01  # Peter: estimated from measurements with syntetic data, the decimate seams to be a bit off, quick and dirty
        array_decimated = CORRECTION_FACTOR * scipy.signal.decimate(array_decimate, DECIMATE_FACTOR, ftype="iir", zero_phase=True)

        assert len(array_decimated) == len(array_decimate) // DECIMATE_FACTOR
        index_from = SAMPLES_LEFT // DECIMATE_FACTOR
        index_to = len(array_decimated) - SAMPLES_RIGHT // DECIMATE_FACTOR
        array_decimated = array_decimated[index_from:index_to]
        return array_decimated


class SampleProcessConfig:
    def __init__(self, configStep):
        self.fir_count = configStep.fir_count
        self.fir_count_skipped = configStep.fir_count_skipped
        self.stepname = configStep.stepname


class Settle:  # pylint: disable=too-many-instance-attributes
    """
    Stream-Sink: Implements a Stream-Interface
    Stream-Source: Drives a output of Stream-Interface
    """

    CALCULATION_INTERVAL_S = 1.0  # Calculate every second
    INVALID_BIG_V = 1000000.0

    def __init__(self, out, config):
        self.out = out
        self.__config = config
        self.__stage = None
        self.__dt_s = None
        self.__TAG_PUSH = None
        self.__calculation_interval_samples = None
        self.__samples = 0
        self.__max_V = -Settle.INVALID_BIG_V
        self.__min_V = +Settle.INVALID_BIG_V
        self.__history_ok = [
            True,
        ] * 10  # 10 Times CALCULATION_INTERVAL_S

    def init(self, stage, dt_s):
        self.__stage = stage
        self.__dt_s = dt_s
        self.__TAG_PUSH = f"Settle {self.__stage}"
        self.__calculation_interval_samples = int(Settle.CALCULATION_INTERVAL_S / self.__dt_s)

        self.out.init(stage=stage, dt_s=dt_s)

    def done(self):
        self.out.done()

    def push(self, array_in):
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        if array_in is not None:
            self.__max_V = max(self.__max_V, array_in.max())
            self.__min_V = min(self.__min_V, array_in.min())

            self.__samples += len(array_in)

            if self.__samples > self.__calculation_interval_samples:
                self.__samples = 0
                self.calculate()
        return self.out.push(array_in)

    def calculate(self):
        LIMIT_V = 2e-07
        ok = self.__max_V < LIMIT_V
        self.__history_ok = [
            ok,
        ] + self.__history_ok[:-1]
        in_limit = max(self.__history_ok)
        logger.info(f"in_limit={in_limit}, history={self.__history_ok}")


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
        self.__config = config
        self.__directory = directory
        self.__stepsize_bins = classify_stepsize.bins_factory()

        self.frequencies = None
        self.__Pxx_sum = None
        self.__Pxx_n = 0
        self.__stage = None
        self.__dt_s = None
        self.__TAG_PUSH = None
        self.__pushcalulator = None
        self.__mode_fifo = None
        self.__fifo = None

    def init(self, stage, dt_s):
        self.__stage = stage
        self.__dt_s = dt_s
        self.__TAG_PUSH = f"Density {self.__stage}"

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

        self.out.init(stage=stage, dt_s=dt_s)

    def done(self):
        self.out.done()

    def push(self, array_in):
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        if array_in is None:
            if (self.__fifo is None) or (len(self.__fifo) < SAMPLES_DENSITY):
                # Not sufficient data
                return self.out.push(None)

            # Time is over. Calculate density
            assert len(self.__fifo) == SAMPLES_DENSITY
            # if len(self.array) != SAMPLES_DENSITY:
            #   logger.debug('Density not calculated')
            # if self.stage >= 4:
            #   logger.debug(f'self.density {self.stage}')
            self.density(self.__fifo)
            if self.__mode_fifo:
                self.__fifo = self.__fifo[self.__pushcalulator.push_size_samples :]
            else:
                self.__fifo = None
            return self.__TAG_PUSH

        assert array_in is not None
        self.out.push(array_in)

        # Add to 'self.array'
        if self.__mode_fifo:
            assert len(array_in) == self.__pushcalulator.push_size_samples
            self.__fifo = np.append(self.__fifo, array_in)
            return None

        assert len(array_in) >= SAMPLES_DENSITY
        self.__fifo = array_in[:SAMPLES_DENSITY]
        logger.debug(f"Density Stage {self.__stage:02d} dt_s {self.__dt_s:016.12f}, len(array_in)={len(array_in)}")

        return None

    def density(self, array):
        logger.debug(f"Density Stage {self.__stage:02d} dt_s {self.__dt_s:016.12f}, len(array)={len(array)} calculation")

        self.frequencies, Pxx = scipy.signal.periodogram(array, 1 / self.__dt_s, window="hamming", detrend="linear")  # Hz, V^2/Hz

        # Averaging
        do_averaging = True
        if do_averaging:
            self.__Pxx_n += 1
            if self.__Pxx_sum is None:
                self.__Pxx_sum = Pxx
            else:
                assert len(self.__Pxx_sum) == len(Pxx)
                self.__Pxx_sum += Pxx
        else:
            self.__Pxx_n = 1
            self.__Pxx_sum = Pxx

        # Stepsize statistics
        stepsizes_V = np.abs(np.diff(array))
        for stepsize_V in stepsizes_V:
            self.__stepsize_bins.add(stepsize_V)

        _filenameFull = program_fir_plot.DensityPlot.save(config=self.__config, directory=self.__directory, stage=self.__stage, dt_s=self.__dt_s, frequencies=self.frequencies, Pxx_n=self.__Pxx_n, Pxx_sum=self.__Pxx_sum, stepsize_bins_count=self.__stepsize_bins.count, stepsize_bins_V=self.__stepsize_bins.V, samples_V=array)

        # if self.stage > 8:
        #   logger.debug(f'{self.stage} ')


class OutTrash:
    """
    Stream-Sink: Implements a Stream-Interface
    """

    def __init__(self):
        self.stage = None
        self.dt_s = None
        self.array = np.empty(0, dtype=NUMPY_FLOAT_TYPE)

    def init(self, stage, dt_s):
        self.stage = stage
        self.dt_s = dt_s

    def done(self):
        pass

    def push(self, array_in):
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        return ""


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

            max_calculations = 30
            for _ in range(max_calculations):
                calculation_stage = self.out.push(None)
                done = len(calculation_stage) == 0
                if done:
                    break


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

    def init(self, stage, dt_s):
        self.stage = stage
        self.total_samples = 0
        self.out.init(stage=stage, dt_s=dt_s)
        self.pushcalulator_next = PushCalculator(dt_s)

    def done(self):
        self.out.done()

    def push(self, array_in):
        """
        If calculation: Return a string explaining which stage calculated.
        Else: Pass to the next stage.
        The last stage will return ''.
        if array_in is not None:
          Return: None
        """
        if array_in is None:
            # Give the next stage a chance to decimate!
            return self.out.push(None)

        self.total_samples += len(array_in)
        self.array = np.append(self.array, array_in)

        push_size_samples = self.pushcalulator_next.push_size_samples
        if len(self.array) >= push_size_samples:
            self.out.push(self.array[:push_size_samples])
            # Save the remainting part to 'self.array'
            self.array = self.array[push_size_samples:]

            max_calculations = 30
            for _i in range(max_calculations):
                calculation_stage = self.out.push(None)
                assert isinstance(calculation_stage, str)
                done = len(calculation_stage) == 0
                if done:
                    return None
            # logger.debug('m', end='')
        return None


class SampleProcess:
    def __init__(self, config, directory_raw):
        assert isinstance(directory_raw, pathlib.Path)

        self.config = config
        self.directory_raw = directory_raw
        o = OutTrash()

        # o = Settle(o, config=config)

        for _i in range(config.fir_count - 1):
            o = Density(o, config=config, directory=self.directory_raw)
            o = FIR(o)

        o = Density(o, config=config, directory=self.directory_raw)
        o = UniformPieces(o)
        self.output = o


if __name__ == "__main__":
    import doctest

    doctest.testmod()
