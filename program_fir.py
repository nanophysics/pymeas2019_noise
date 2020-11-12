import math
import time
import pickle
import pathlib
import logging
import itertools
import threading

import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import program_eseries
import program_classify
import library_topic

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


FILENAME_TAG_SKIP = "_SKIP"


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
            return False

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

        _filenameFull = DensityPlot.save(config=self.__config, directory=self.__directory, stage=self.__stage, dt_s=self.__dt_s, frequencies=self.frequencies, Pxx_n=self.__Pxx_n, Pxx_sum=self.__Pxx_sum, stepsize_bins_count=self.__stepsize_bins.count, stepsize_bins_V=self.__stepsize_bins.V, samples_V=array)

        # if self.stage > 8:
        #   logger.debug(f'{self.stage} ')


class DensityPlot:  # pylint: disable=too-many-instance-attributes
    @classmethod
    def save(cls, config, directory, stage, dt_s, frequencies, Pxx_n, Pxx_sum, stepsize_bins_count, stepsize_bins_V, samples_V):  # pylint: disable=too-many-arguments
        assert isinstance(directory, pathlib.Path)

        skip = stage < config.fir_count_skipped
        skiptext = FILENAME_TAG_SKIP if skip else ""
        filename = f"densitystep_{config.stepname}_{stage:02d}{skiptext}.pickle"
        data = {
            "stepname": config.stepname,
            "stage": stage,
            "dt_s": dt_s,
            "frequencies": frequencies,
            "Pxx_n": Pxx_n,
            "Pxx_sum": Pxx_sum,
            "skip": skip,
            "stepsize_bins_count": stepsize_bins_count,
            "stepsize_bins_V": np.array(stepsize_bins_V, dtype=NUMPY_FLOAT_TYPE),
            "samples_V": samples_V,
        }
        directory.mkdir(parents=True, exist_ok=True)
        filenameFull = directory / filename
        with filenameFull.open("wb") as f:
            pickle.dump(data, f)

        return filenameFull

    @classmethod
    def file_changed(cls, dir_input):
        filename_summary = library_topic.PickleResultSummary.filename(dir_input)
        timestamp_summary = 0.0
        if filename_summary.exists():
            timestamp_summary = filename_summary.stat().st_mtime
        for pickle_file in cls.pickle_files_from_directory(dir_input=dir_input, skip=True):
            if pickle_file.stat().st_mtime > timestamp_summary:
                # At least one file is newer
                return True
        # No file has changed
        return False

    @classmethod
    def pickle_files_from_directory(cls, dir_input, skip):
        """
        Return all plot (.pickle-files) from directory.
        """
        for filename in pathlib.Path(dir_input).glob("densitystep_*.pickle"):
            if skip and (FILENAME_TAG_SKIP in filename.name):
                continue
            yield filename

    @classmethod
    def plots_from_directory(cls, dir_input, skip):
        """
        Return all plot (.pickle-files) from directory.
        """
        # return [DensityPlot(filename) for filename in cls.pickle_files_from_directory(dir_input, skip)]
        l = []
        for filename in cls.pickle_files_from_directory(dir_input, skip):
            try:
                dp = DensityPlot(filename)
                l.append(dp)
            except pickle.UnpicklingError as e:
                logger.error(f"Unpicking f{filename}: {e}")
                logger.exception(e)
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"Read f{filename}: {e}")
                logger.exception(e)
        return l

    @classmethod
    def directory_plot(cls, directory_in, dir_plot):
        """
        Loop for all densitystage-files in directory and plot.
        """
        for densityPeriodogram in cls.plots_from_directory(directory_in, skip=False):
            densityPeriodogram.plot(dir_plot)

    @classmethod
    def directory_plot_thread(cls, dir_input, dir_plot):
        class WorkerThread(threading.Thread):
            def __init__(self, *args, **keywords):
                threading.Thread.__init__(self, *args, **keywords)
                self.__stop = False
                self.start()

            def run(self):
                while True:
                    time.sleep(2.0)
                    cls.directory_plot(dir_input, dir_plot)
                    if self.__stop:
                        return

            def stop(self):
                self.__stop = True
                self.join()

        return WorkerThread()

    def sort_key(self):
        assert isinstance(self, DensityPlot)
        return self.stepname, self.dt_s

    def __init__(self, filename):
        with open(filename, "rb") as f:
            data = pickle.load(f)
        self.stepname = data["stepname"]
        self.stage = data["stage"]
        self.dt_s = data["dt_s"]
        self.skip = data["skip"]
        self.frequencies = data["frequencies"]
        self.__Pxx_n = data["Pxx_n"]
        self.__Pxx_sum = data["Pxx_sum"]
        self.stepsize_bins_count = data["stepsize_bins_count"]
        self.stepsize_bins_V = data["stepsize_bins_V"]
        self.samples_V = data["samples_V"]
        # logger.debug(f'DensityPlot {self.stage} {self.dt_s} {filename}')

    @property
    def Pxx_n(self):
        return self.__Pxx_n

    @property
    def Pxx(self):
        if self.__Pxx_n == 0:
            return None
        return self.__Pxx_sum / self.__Pxx_n

    @property
    def Dxx(self):
        if self.__Pxx_n == 0:
            return None
        return np.sqrt(self.Pxx)  # V/Hz^0.5

    def plot(self, directory):
        assert isinstance(directory, pathlib.Path)

        directory.mkdir(parents=True, exist_ok=True)
        filenameFull = directory / f"densitystep_{self.stepname}_{self.stage:02d}_{self.dt_s:016.12f}.png"
        if self.Pxx_n is None:
            logger.info(f"No Pxx: skipped {filenameFull}")
            return

        # If we have averaged values, use it
        fig, ax = plt.subplots()
        color = "fuchsia" if self.Pxx_n == 1 else "blue"
        ax.loglog(self.frequencies, self.Dxx, linewidth=0.1, color=color)
        plt.ylabel(f"Density stage dt_s {self.dt_s:.3e}s ")
        # plt.ylim( 1e-8,1e-6)

        # plt.xlim(1e2, 1e5)
        f_limit_low = 1.0 / self.dt_s / 2.0 * Selector.USEFUL_PART
        f_limit_high = 1.0 / self.dt_s / 2.0
        plt.axvspan(f_limit_low, f_limit_high, color="red", alpha=0.2)
        plt.grid(True)
        fig.savefig(filenameFull)
        fig.clf()
        plt.close(fig)
        plt.clf()
        plt.close()


class DensityPoint:
    DELIMITER = "\t"

    def __init__(self, f, d, enbw, densityPlot):
        self.f = f
        self.d = d
        self.enbw = enbw
        self.__densityPlot = densityPlot

    @property
    def stage(self):
        return self.__densityPlot.stage

    @property
    def step(self):
        return self.__densityPlot.step

    @property
    def stepname(self):
        return self.__densityPlot.stepname

    @property
    def skip(self):
        return self.__densityPlot.skip

    @property
    def line(self):
        l = (self.stepname, str(self.stage), bool(self.skip), self.f, self.d)
        l = [str(e) for e in l]
        return DensityPoint.DELIMITER.join(l)

    # @classmethod
    # def factory(cls, line):
    #   class DensityPointRead:
    #     def __init__(self, line):
    #       l = line.split(cls.DELIMITER)
    #       self.stepname = l[0]
    #       self.stage = int(l[1])
    #       self.skip = bool(l[2])
    #       self.f = float(l[3])
    #       self.d = float(l[4])

    #   return DensityPointRead(line)


class Average:
    def __init__(self):
        self.reset()

    def reset(self):
        self.__sum_d = 0.0
        self.__sum_n = 0

    def avg(self):
        """
        return None if no samples
        """
        if self.__sum_n == 0:
            return None
        avg = self.__sum_d / self.__sum_n
        self.reset()
        return avg

    def sum(self, d):
        self.__sum_n += 1
        self.__sum_d += d


class Selector:
    USEFUL_PART = 0.75  # depending on the downsampling, useful part is the non influenced part by the low pass filtering of the FIR stage

    def __init__(self, series="E12"):
        self.__eseries_borders = program_eseries.eseries(series=series, minimal=1e-6, maximal=1e8, borders=True)

    def fill_bins(self, density, firstDensityPoint, lastDensity, trace=False):
        # contribute, fill_bins
        assert isinstance(density, DensityPlot)
        avg = Average()
        idx_fft = 0
        Pxx = density.Pxx
        list_density_points = []

        fmax_Hz = 1.0 / (density.dt_s * 2.0)  # highest frequency in spectogram
        f_high_limit_Hz = Selector.USEFUL_PART * fmax_Hz
        f_low_limit_Hz = f_high_limit_Hz / DECIMATE_FACTOR  # every FIR stage reduces sampling frequency by factor DECIMATE_FACTOR

        for f_eserie_left, f_eserie, f_eserie_right in self.__eseries_borders:
            if not trace:
                if f_eserie < f_low_limit_Hz:
                    if not firstDensityPoint:
                        continue
                    # Special case for the first point: select low frequencies too

                if f_eserie > f_high_limit_Hz:
                    if not lastDensity:
                        # We are finished with this loop
                        # TodoHans: save above frequency_complete_low_limit here if P is None?
                        return list_density_points
                    # Special case for the last point: select high frequencies too

            while True:
                if idx_fft >= len(density.frequencies):
                    # We are finished with this loop
                    return list_density_points

                f_fft = density.frequencies[idx_fft]

                if f_fft < f_eserie_left:
                    idx_fft += 1
                    continue

                if f_fft > f_eserie_right:
                    P = avg.avg()
                    if P is not None:
                        d = math.sqrt(P)
                        dp = DensityPoint(f=f_eserie, d=d, densityPlot=density, enbw=f_eserie_right - f_eserie_left)
                        list_density_points.append(dp)
                    break  # Continue in next eserie.

                d = Pxx[idx_fft]
                avg.sum(d)
                idx_fft += 1

        raise Exception("Internal Programming Error")


class ColorRotator:
    # https://stackoverflow.com/questions/22408237/named-colors-in-matplotlibpy
    COLORS = "bgrcmykw"  # Attention: White at the end!
    COLORS = "bgrcmyk"
    COLORS = (
        "blue",
        "orange",
        "black",
        "green",
        "red",
        "cyan",
        "magenta",
        # 'yellow',
    )

    def __init__(self):
        self.iter = itertools.cycle(ColorRotator.COLORS)

    @property
    def color(self):
        return next(self.iter)


class LsdSummary:
    def __init__(self, list_density, directory, trace=False):
        self.__directory = directory
        self.__trace = trace
        self.__list_density_points = []
        self.__dict_stages = {}

        list_density = sorted(list_density, key=DensityPlot.sort_key, reverse=True)
        for density in list_density:
            self.__dict_stages[density.stage] = dict(
                stage=density.stage,
                dt_s=density.dt_s,
                stepsize_bins_V=density.stepsize_bins_V,
                stepsize_bins_count=density.stepsize_bins_count,
                samples_V=density.samples_V,
            )

        for density in list_density:
            assert isinstance(density, DensityPlot)
            Pxx = density.Pxx
            if Pxx is None:
                continue

            selector = Selector("E12")
            first_density_point = len(self.__list_density_points) == 0
            last_density = density == list_density[-1]
            list_density_points = selector.fill_bins(density, firstDensityPoint=first_density_point, lastDensity=last_density, trace=self.__trace)
            self.__list_density_points.extend(list_density_points)

    def write_summary_file(self, trace):
        file_tag = "_trace" if trace else ""
        filename_summary = f"{self.__directory}/result_summary_LSD{file_tag}.txt"
        with open(filename_summary, "w") as f:
            for dp in self.__list_density_points:
                f.write(dp.line)
                f.write("\n")

    def write_summary_pickle(self):
        f = [dp.f for dp in self.__list_density_points if not dp.skip]
        d = [dp.d for dp in self.__list_density_points if not dp.skip]
        enbw = [dp.enbw for dp in self.__list_density_points if not dp.skip]
        library_topic.PickleResultSummary.save(self.__directory, f, d, enbw, self.__dict_stages)

    def plot(self, file_tag=""):  # pylint: disable=too-many-locals
        fig, ax = plt.subplots()

        # https://matplotlib.org/3.1.1/api/markers_api.html
        MARKERS = ".+x*"
        colorRotator = ColorRotator()

        stepnames = [(stepname, list(g)) for stepname, g in itertools.groupby(self.__list_density_points, lambda density: density.stepname)]
        for stepnumber, (_stepname, list_step_density) in enumerate(stepnames):

            stages = [(stage, list(g)) for stage, g in itertools.groupby(list_step_density, lambda dp: dp.stage)]
            for _stage, list_density_points in stages:
                f = [dp.f for dp in list_density_points]
                d = [dp.d for dp in list_density_points]
                color = color_fancy = colorRotator.color
                linestyle = "none"
                marker = "."
                markersize = 3
                if self.__trace:
                    linestyle = "-"
                    color = color_fancy
                    dp = list_density_points[0]
                    marker = MARKERS[stepnumber % len(MARKERS)]
                    markersize = 2 if dp.skip else 4
                ax.loglog(f, d, linestyle=linestyle, linewidth=0.1, marker=marker, markersize=markersize, color=color)

        plt.ylabel(f"Density [V/Hz^0.5]")
        plt.xlabel(f"Frequency [Hz]")
        # plt.ylim( 1e-11,1e-6)
        # plt.xlim(1e-2, 1e5) # temp Peter
        # plt.grid(True)
        plt.grid(True, which="major", axis="both", linestyle="-", color="gray", linewidth=0.5)
        plt.grid(True, which="minor", axis="both", linestyle="-", color="silver", linewidth=0.1)
        ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=30))
        filebase = f"{self.__directory}/result_summary_LSD{file_tag}"
        logger.info(f" Summary LSD {filebase}")
        fig.savefig(filebase + ".png", dpi=300)
        # fig.savefig(filebase+'.svg')
        # plt.show()
        fig.clf()
        plt.close(fig)
        plt.clf()
        plt.close()


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


class InSyntetic:
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

        for _i in range(config.fir_count - 1):
            o = Density(o, config=config, directory=self.directory_raw)
            o = FIR(o)

        o = Density(o, config=config, directory=self.directory_raw)
        o = UniformPieces(o)
        self.output = o


if __name__ == "__main__":
    import doctest

    doctest.testmod()
