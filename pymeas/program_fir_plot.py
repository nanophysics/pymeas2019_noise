import re
import math
import time
import pickle
import pathlib
import logging
import itertools
import threading

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from . import program_eseries
from . import program_fir
from . import library_topic

logger = logging.getLogger("logger")


class FilenameDensityStepMatcher:
    FILENAME_TAG_SKIP = "_SKIP"
    GLOB_PATTERN = "densitystep_*.pickle"
    PATTERN = fr"^densitystep_(?P<stepname>.*?)_(?P<stage>\d+)(?P<skiptext>{FILENAME_TAG_SKIP})?.pickle$"
    RE = re.compile(PATTERN)

    @classmethod
    def filename_from_stepname_stage(cls, stepname: str, stage: int, skip: bool):
        assert isinstance(stepname, str)
        assert isinstance(stage, int)
        assert isinstance(skip, bool)
        skiptext = cls.FILENAME_TAG_SKIP if skip else ""
        return f"densitystep_{stepname}_{stage:02d}{skiptext}.pickle"

    def __init__(self, filename):
        assert isinstance(filename, str)
        _match = FilenameDensityStepMatcher.RE.match(filename)
        self.match = _match is not None
        self.stepname = None
        self.stage = None
        self.skip = None
        self.label = None
        if self.match:
            self.stepname = _match.group("stepname")
            self.stage = _match.group("stage")
            self.label = f"{self.stepname}_{self.stage}"
            skiptext = _match.group("skiptext")
            self.skip = skiptext == FilenameDensityStepMatcher.FILENAME_TAG_SKIP


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


class DensityPlot:  # pylint: disable=too-many-instance-attributes
    @classmethod
    def save(cls, config, directory, stage, dt_s, frequencies, Pxx_n, Pxx_sum, stepsize_bins_count, stepsize_bins_V, samples_V):  # pylint: disable=too-many-arguments
        assert isinstance(directory, pathlib.Path)
        assert isinstance(stage, int)
        assert isinstance(dt_s, float)
        assert isinstance(frequencies, np.ndarray)
        assert isinstance(Pxx_n, int)
        assert isinstance(Pxx_sum, np.ndarray)
        assert isinstance(stepsize_bins_count, np.ndarray)
        assert isinstance(stepsize_bins_V, list)
        assert isinstance(samples_V, np.ndarray)

        skip = stage < config.fir_count_skipped
        filename = FilenameDensityStepMatcher.filename_from_stepname_stage(stepname=config.stepname, stage=stage, skip=skip)
        data = {
            "stepname": config.stepname,
            "stage": stage,
            "dt_s": dt_s,
            "frequencies": frequencies,
            "Pxx_n": Pxx_n,
            "Pxx_sum": Pxx_sum,
            "skip": skip,
            "stepsize_bins_count": stepsize_bins_count,
            "stepsize_bins_V": np.array(stepsize_bins_V, dtype=program_fir.NUMPY_FLOAT_TYPE),
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
        assert isinstance(dir_input, pathlib.Path)
        assert isinstance(skip, bool)

        for filename in dir_input.glob(FilenameDensityStepMatcher.GLOB_PATTERN):
            m = FilenameDensityStepMatcher(filename.name)
            if skip and m.skip:
                continue
            yield filename

    @classmethod
    def plots_from_directory(cls, dir_input, skip):
        """
        Return all plot (.pickle-files) from directory.
        """
        assert isinstance(dir_input, pathlib.Path)
        assert isinstance(skip, bool)

        # return [DensityPlot(filename) for filename in cls.pickle_files_from_directory(dir_input, skip)]
        l = []
        for filename in cls.pickle_files_from_directory(dir_input, skip):
            dp = DensityPlot(filename)
            l.append(dp)
        return l

    @classmethod
    def directory_plot_obsolete(cls, directory_in, dir_plot):
        """
        Loop for all densitystage-files in directory and plot.
        """
        for densityPeriodogram in cls.plots_from_directory(directory_in, skip=False):
            densityPeriodogram.plot(dir_plot)

    @classmethod
    def directory_plot_thread_obsolete(cls, dir_input, dir_plot):
        class WorkerThread(threading.Thread):
            def __init__(self, *args, **keywords):
                threading.Thread.__init__(self, *args, **keywords)
                self.__stop = False
                self.start()

            def run(self):
                while True:
                    time.sleep(2.0)
                    cls.directory_plot_obsolete(dir_input, dir_plot)
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
        retry = 0
        while True:
            try:
                with open(filename, "rb") as f:
                    data = pickle.load(f)
                    break
            except Exception as e:  # pylint: disable=broad-except
                logger.debug(f"Unpicking {filename}: {e}")
                # We could not read the file. probably because the measureing process was writing it just now.
                # Lets try again!
                retry += 1
                if retry >= 3:
                    raise
                time.sleep(0.05)
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
        f_low_limit_Hz = f_high_limit_Hz / program_fir.DECIMATE_FACTOR  # every FIR stage reduces sampling frequency by factor DECIMATE_FACTOR

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
        assert isinstance(list_density, list)
        assert isinstance(directory, pathlib.Path)
        assert isinstance(trace, bool)

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
