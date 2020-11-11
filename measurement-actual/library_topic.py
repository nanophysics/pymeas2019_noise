import re
import time
import types
import pickle
import pathlib
import numpy as np

DIRECTORY_NAME_RAW_PREFIX = "raw-"


class ResultAttributes:
    RESULT_DIR_PATTERN = "raw-*"
    REG_DIR = re.compile(r"^raw-(?P<color>.+?)-(?P<topic>.+)$")

    def __init__(self, dir_raw):
        self.dir_raw = dir_raw
        match = ResultAttributes.REG_DIR.match(dir_raw.name)
        if match is None:
            raise Exception(f'Expected directory {dir_raw.name} to match the pattern "result-color-topic"!')
        d = match.groupdict()
        self.color = d["color"]
        self.topic = d["topic"]

    @classmethod
    def getdatetime(cls):
        return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    @classmethod
    def result_dir_actual(cls, directory_name=None):
        if directory_name is None:
            return f"{DIRECTORY_NAME_RAW_PREFIX}red-{cls.getdatetime()}"
        assert directory_name.startswith(DIRECTORY_NAME_RAW_PREFIX)
        return directory_name


class PickleResultSummary:
    def __init__(self, f, d, enbw, dict_stages):
        self.f = f
        self.d = d
        self.enbw = enbw
        self.dict_stages = dict_stages

        self.x_filename = None
        self.x_directory = None

    def __getstate__(self):
        # Only these elements will be pickled
        return {"f": self.f, "d": self.d, "enbw": self.enbw, "dict_stages": self.dict_stages}

    @classmethod
    def filename(cls, directory):
        return directory / "result_summary.pickle"

    @classmethod
    def save(cls, directory, f, d, enbw, dict_stages):  # pylint: disable=too-many-arguments
        prs = PickleResultSummary(f, d, enbw, dict_stages)
        filename_summary_pickle = cls.filename(directory)
        with open(filename_summary_pickle, "wb") as fout:
            pickle.dump(prs, fout)

    @classmethod
    def load(cls, directory):
        filename_summary_pickle = cls.filename(directory)
        prs = None
        if filename_summary_pickle.exists():
            with open(filename_summary_pickle, "rb") as fin:
                try:
                    prs = pickle.load(fin)
                except pickle.UnpicklingError as e:
                    print(f"ERROR Unpicking f{filename_summary_pickle.name}: {e}")
            assert isinstance(prs, PickleResultSummary)
        if prs is None:
            # The summary file has not been calculated yet.
            prs = PickleResultSummary(f=[], d=[], enbw=[], dict_stages={})
        prs.x_directory = directory
        prs.x_filename = filename_summary_pickle
        try:
            prs.dict_stages
        except AttributeError:
            prs.dict_stages = {}

        return prs

    def reload_if_changed(self):
        import run_1_condense

        changed = run_1_condense.reload_if_changed(self.x_directory)
        if changed:
            # File has changed
            prs = PickleResultSummary.load(self.x_directory)
            self.f = prs.f
            self.d = prs.d
            self.enbw = prs.enbw
            self.dict_stages = prs.dict_stages

        return changed


class Topic:
    def __init__(self, ra, prs):
        assert isinstance(ra, ResultAttributes)
        assert isinstance(prs, PickleResultSummary)
        self.__ra = ra
        self.__prs = prs
        self.__plot_line = None
        self.toggle = True

    def get_as_dict(self):
        return dict(
            topic=self.topic,
            raw_data=dict(
                d=self.d,
                f=self.f,
                enbw=self.enbw,
            ),
            presentations=PRESENTATIONS.get_as_dict(self),
        )

    def set_plot_line(self, plot_line):
        self.__plot_line = plot_line

    def reload_if_changed(self, presentation):
        assert self.__plot_line is not None
        # start = time.time()
        changed = self.__prs.reload_if_changed()
        if changed:
            self.recalculate_data(presentation)
            # print(f'changed {time.time()-start:0.2f}s "{self.__ra.topic}"')
            print(f'plot: reload changed data: "{self.__ra.topic}"')
        return changed

    def recalculate_data(self, presentation):
        x, y = presentation.get_xy(self)
        assert len(x) == len(y)
        self.__plot_line.set_data(x, y)

    def clear_line(self):
        if self.__plot_line is None:
            return
        self.__plot_line.remove()
        del self.__plot_line
        self.__plot_line = None

    @classmethod
    def load(cls, dir_raw):
        prs = PickleResultSummary.load(dir_raw)
        ra = ResultAttributes(dir_raw=dir_raw)
        return Topic(ra, prs)

    @property
    def topic(self):
        return self.__ra.topic

    @property
    def color(self):
        return self.__ra.color

    def get_stepsize(self, stage):
        assert isinstance(stage, int)
        dict_stage = self.__prs.dict_stages.get(stage, None)
        if dict_stage is None:
            return ((0.0, 1.0), (0.0, 1.0))
        stepsize_bins_count = dict_stage["stepsize_bins_count"]
        stepsize_bins_V = dict_stage["stepsize_bins_V"]
        # Mask all array-elements with bins_count == 0
        # stepsize_bins_count = np.ma.masked_equal(stepsize_bins_count, 0)
        stepsize_bins_V = np.ma.masked_where(stepsize_bins_count == 0, stepsize_bins_V)
        stepsize_bins_count = np.ma.masked_where(stepsize_bins_count == 0, stepsize_bins_count)
        stepsize_bins_V = stepsize_bins_V.compressed()  # pylint: disable=no-member
        stepsize_bins_count = stepsize_bins_count.compressed()  # pylint: disable=no-member
        return (stepsize_bins_V, stepsize_bins_count)

    def get_timeserie(self, stage):
        assert isinstance(stage, int)
        dict_stage = self.__prs.dict_stages.get(stage, None)
        if dict_stage is None:
            return ((0.0, 1.0), (0.0, 1.0))
        samples_V = dict_stage["samples_V"]
        dt_s = dict_stage["dt_s"]
        # TODO(Hans): Cash this array
        x = np.linspace(start=0.0, stop=dt_s * len(samples_V), num=len(samples_V))
        return (x, samples_V)

    @property
    def f(self):
        return self.__prs.f

    @property
    def d(self):
        return self.__prs.d

    @property
    def enbw(self):
        return self.__prs.enbw

    @property
    def scaling_LSD(self):
        return self.d

    @property
    def scaling_PSD(self):
        return np.square(self.d)

    @property
    def scaling_LS(self):
        return np.multiply(self.d, np.sqrt(self.enbw))

    @property
    def scaling_PS(self):
        return np.multiply(self.scaling_PSD, self.enbw)

    @property
    def scaling_INTEGRAL(self):
        return np.sqrt(np.cumsum(self.scaling_PS))  # todo: start sum above frequency_complete_low_limit

    @property
    def decade_f_d(self):
        """
        return f, d
        """
        return self.__xy_decade_from_INTEGRAL(self.f, self.scaling_INTEGRAL)

    def __xy_decade_from_INTEGRAL(self, f, v):
        """
        Returns frequency and density per decade.
        """
        f_decade = []
        value_decade = []
        last_value = None

        def is_border_decade(f):
            return abs(f * 10 ** -(round(np.log10(f))) - 1.0) < 1e-6

        for (_f, value) in zip(f, v):
            if is_border_decade(_f):
                if last_value is not None:
                    f_decade.append(_f)
                    value_decade.append(np.sqrt(value ** 2 - last_value ** 2))
                last_value = value
        return f_decade, value_decade


class Presentation:
    def __init__(self, tag, help_text, xy_func, x_label, y_label, logarithmic_scales=True):  # pylint: disable=too-many-arguments
        assert isinstance(tag, str)
        assert isinstance(help_text, str)
        assert isinstance(xy_func, types.FunctionType)
        assert isinstance(y_label, str)
        assert isinstance(x_label, str)
        assert isinstance(logarithmic_scales, bool)
        self.tag = tag
        self.help_text = help_text
        self.__xy_func = xy_func
        self.x_label = x_label
        self.y_label = y_label
        self.logarithmic_scales = logarithmic_scales

    def get_xy(self, topic):
        stage = 2
        return self.__xy_func(topic, stage)

    def get_as_dict(self, topic):
        x, y = self.get_xy(topic)
        return dict(
            tag=self.tag,
            help_text=self.help_text,
            x_label=self.x_label,
            y_label=self.y_label,
            x=x,
            y=y,
        )

    @property
    def title(self):
        return f"{self.tag}: {self.y_label}"


X_LABEL = "Frequency [Hz]"


class Presentations:
    def __init__(self):
        self.list = (
            Presentation(
                tag="LSD",
                x_label=X_LABEL,
                y_label="linear spectral density [V/Hz^0.5]",
                help_text="linear spectral density [V/Hz^0.5] represents the noise density. Useful to describe random noise.",
                xy_func=lambda topic, stage: (topic.f, topic.scaling_LSD),
            ),
            Presentation(tag="PSD", x_label=X_LABEL, y_label="power spectral density [V^2/Hz]", help_text="power spectral density [V^2/Hz] ist just the square of the LSD. This representation of random noise is useful if you want to sum up the signal over a given frequency interval. ", xy_func=lambda topic, stage: (topic.f, topic.scaling_PSD)),
            Presentation(tag="LS", x_label=X_LABEL, y_label="linear spectrum [V rms]", help_text="linear spectrum [V rms] represents the voltage in a frequency range. Useful if you want to measure the amplitude of a sinusoidal signal.", xy_func=lambda topic, stage: (topic.f, topic.scaling_LS)),
            Presentation(
                tag="PS",
                x_label=X_LABEL,
                y_label="power spectrum [V^2]",
                help_text="power spectrum [V^2] represents the square of LS. Useful if you want to measure the amplitude of a sinusoidal signal which is just between two frequency bins. You can now add the two values to get the amplitude of the sinusoidal signal.",
                xy_func=lambda topic, stage: (topic.f, topic.scaling_PS),
            ),
            Presentation(
                tag="INTEGRAL",
                x_label=X_LABEL,
                y_label="integral [V rms]",
                help_text="integral [V rms] represents the integrated voltage from the lowest measured frequency up to the actual frequency. Example: Value at 1 kHz: is the voltage between 0.01 Hz and 1 kHz.",
                xy_func=lambda topic, stage: (topic.f, topic.scaling_INTEGRAL),
            ),
            Presentation(tag="DECADE", x_label=X_LABEL, y_label="decade left of the point [V rms]", help_text="decade left of the point [V rms] Example: The value at 100 Hz represents the voltage between 100Hz/10 = 10 Hz and 100 Hz.", xy_func=lambda topic, stage: topic.decade_f_d),
            Presentation(tag="STEPSIZE", x_label="stepsize [V]", y_label="count samples [samples/s]", help_text="TODO.", xy_func=lambda topic, stage: topic.get_stepsize(stage)),
            Presentation(tag="TIMESERIE", x_label="timeserie [s]", y_label="sample [V]", help_text="TODO.", xy_func=lambda topic, stage: topic.get_timeserie(stage), logarithmic_scales=False),
        )

        self.tags = [p.tag for p in self.list]
        self.dict = {p.tag: p for p in self.list}

    def get(self, tag):
        try:
            return self.dict[tag]
        except KeyError:
            raise Exception(f"Presentation {tag} not found! Choose one of {self.tags}.")

    def get_as_dict(self, topic):
        return {p.tag: p.get_as_dict(topic) for p in self.list}


PRESENTATIONS = Presentations()


class PlotDataMultipleDirectories:
    def __init__(self, filename):
        self.topdir = pathlib.Path(filename).absolute().parent
        self.__load_data()

    def __load_data(self):
        list_directories = self.read_directories()
        self.set_directories = {d.name for d in list_directories}
        self.listTopics = [Topic.load(d) for d in list_directories]
        self.listTopics.sort(key=lambda topic: topic.topic.upper())

    def read_directories(self):
        list_directories = []
        for dir_raw in self.topdir.glob(ResultAttributes.RESULT_DIR_PATTERN):
            if not dir_raw.is_dir():
                continue
            list_directories.append(dir_raw)
        return list_directories

    def directories_changed(self):
        set_directories_new = {d.name for d in self.read_directories()}
        return self.set_directories != set_directories_new

    def remove_lines(self, fig, ax):
        for topic in self.listTopics:
            topic.clear_line()
        # if len(ax.lines) > 0:
        if ax.has_data() > 0:
            ax.legend().remove()

    def remove_lines_and_reload_data(self, fig, ax):
        self.remove_lines(fig, ax)

        self.__load_data()

        fig.canvas.draw()


class PlotDataSingleDirectory:
    def __init__(self, dir_raw):
        self.listTopics = [Topic.load(dir_raw)]

    def remove_lines(self, fig, ax):
        # TODO(hans): Merge with other method of the same name
        for topic in self.listTopics:
            topic.clear_line()
        # if len(ax.lines) > 0:
        if ax.has_data() > 0:
            ax.legend().remove()
