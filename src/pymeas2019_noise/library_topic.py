import logging
import math
import pathlib
import pickle
import re
import sys
import time
import types

import numpy as np

from . import library_plot_config

logger = logging.getLogger("logger")

DIRECTORY_NAME_RAW_PREFIX = "raw-"


class Stage100msNotFoundException(Exception):
    pass

class FrequencyNotFound(Exception):
    pass

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
    def result_dir_actual(cls, dir_arg=None):
        if dir_arg is None:
            return f"{DIRECTORY_NAME_RAW_PREFIX}red-{cls.getdatetime()}"
        assert dir_arg.startswith(DIRECTORY_NAME_RAW_PREFIX)
        return dir_arg


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
        assert isinstance(directory, pathlib.Path)

        return directory / "result_summary.pickle"

    @classmethod
    def save(cls, directory, f, d, enbw, dict_stages):  # pylint: disable=too-many-arguments
        assert isinstance(directory, pathlib.Path)

        prs = PickleResultSummary(f, d, enbw, dict_stages)
        filename_summary_pickle = cls.filename(directory)
        with open(filename_summary_pickle, "wb") as fout:
            pickle.dump(prs, fout)

    @classmethod
    def load(cls, directory):
        assert isinstance(directory, pathlib.Path)

        filename_summary_pickle = cls.filename(directory)
        prs = None
        if filename_summary_pickle.exists():
            with filename_summary_pickle.open("rb") as fin:
                # For compatibility with the old source structure
                # May be remove when old pickle files have gone.
                sys.modules["library_topic"] = sys.modules["pymeas.library_topic"]
                try:
                    prs = pickle.load(fin)
                except pickle.UnpicklingError as e:
                    logger.error(f"ERROR Unpicking f{filename_summary_pickle.name}: {e}")
                    logger.exception(e)
            assert isinstance(prs, PickleResultSummary)
        if prs is None:
            # The summary file has not been calculated yet.
            prs = PickleResultSummary(f=[], d=[], enbw=[], dict_stages={})

        prs.x_directory = directory
        prs.x_filename = filename_summary_pickle
        try:
            prs.dict_stages  # noqa: B018
        except AttributeError:
            prs.dict_stages = {}

        return prs

    def reload_if_changed(self):
        import run_1_condense

        changed = run_1_condense.reload_if_changed(dir_raw=self.x_directory)
        if changed:
            # File has changed
            prs = PickleResultSummary.load(self.x_directory)
            self.f = prs.f
            self.d = prs.d
            self.enbw = prs.enbw
            self.dict_stages = prs.dict_stages

        return changed


class Stage:
    # TODO(Hans): Why no reuse 'class Densityplot'?
    def __init__(self, topic, dict_stage):
        assert isinstance(topic, Topic)
        self.__topic = topic
        self.stage = dict_stage["stage"]
        self.dt_s = dict_stage["dt_s"]
        self.stepsize_bins_V = dict_stage["stepsize_bins_V"]
        self.stepsize_bins_count = dict_stage["stepsize_bins_count"]
        self.samples_V = dict_stage["samples_V"]
        assert isinstance(self.stage, int)
        assert isinstance(self.dt_s, float)

    @property
    def label(self):
        return f"{self.stage} dt={self.dt_s:0.2e}s"

    def belongs_to_topic(self, topic):
        return self.__topic == topic


class TopicMinusBasenoise:
    """
    This is a small wrapper around 'Topic'.
    If there is a basenoise which has to be subtracted, this wrapper
    caches the difference between noise and base noise.
    """

    def __init__(self, topic):
        assert topic.basenoise is not None
        self._topic = topic
        self.resized_f_d = ResizedArrays(topic.f, topic.basenoise.f, topic.d, topic.basenoise.d)

    @property
    def f(self):
        return self.resized_f_d.f

    @property
    def decade_f_d(self):
        return self._topic.decade_f_d

    @property
    def scaling_LSD(self):
        # beide quadrieren, substrahieren, wurzel
        m = np.square(self.resized_f_d.y) - np.square(self.resized_f_d.base_y)
        m = m.clip(min=0)
        return np.sqrt(m)

    @property
    def scaling_PSD(self):
        # subtrahieren
        m = np.square(self.resized_f_d.y) - np.square(self.resized_f_d.base_y)
        return m.clip(min=0)

    # @property
    # def scaling_LS(self):
    # Peter: soll nicht implementiert werden weil es keinen Sinn macht.
    #     return self.scaling_LSD

    # @property
    # def scaling_PS(self):
    # Peter: soll nicht implementiert werden weil es keinen Sinn macht.
    #     return self.scaling_PSD

    # @property
    # def scaling_INTEGRAL(self):
    # Peter: soll nicht implementiert werden weil es schwierig zu interpretieren ist.
    #     return self.scaling_LSD

    # @property
    # def scaling_DECADE(self):
    #     # Peter: soll nicht implementiert werden weil es schwierig zu interpretieren ist.
    #     return self.scaling_LSD


class Topic:  # pylint: disable=too-many-public-methods
    TAG_BASENOISE = "BASENOISE"

    def __init__(self, ra, prs, dir_raw, plot_config: library_plot_config.PlotConfig, presentations:"Presentations"):
        assert isinstance(ra, ResultAttributes)
        assert isinstance(prs, PickleResultSummary)
        assert isinstance(dir_raw, pathlib.Path)
        assert isinstance(plot_config, library_plot_config.PlotConfig)
        assert isinstance(presentations, Presentations)
        self.__ra = ra
        self.__prs = prs
        self.__plot_line = None
        self._plot_config = plot_config
        self._presentations = presentations
        self.dir_raw = dir_raw
        self.toggle = True
        self.is_basenoise = ra.topic.startswith(Topic.TAG_BASENOISE)
        self.basenoise = None

    @property
    def topic_minus_basenoise(self):
        return TopicMinusBasenoise(self)

    def get_as_dict(self):
        return dict(  # noqa: C408
            topic=self.topic,
            raw_data=dict(  # noqa: C408
                d=self.d,
                f=self.f,
                enbw=self.enbw,
            ),
            presentations=self._presentations.get_as_dict(self),
        )

    def reset_plot_line(self):
        self.__plot_line = None

    def remove_line(self):
        assert self.__plot_line is not None
        self.__plot_line.remove()
        self.__plot_line = None

    def set_plot_line(self, plot_line):
        assert self.__plot_line is None
        self.__plot_line = plot_line

    def set_basenoise(self, basenoise):
        assert isinstance(basenoise, Topic)
        assert self.basenoise is None
        self.basenoise = basenoise

    def reload_if_changed(self, presentation, stage):
        assert isinstance(stage, None | Stage)
        if self.__plot_line is None:
            logger.warning(f"'self.__plot_line is None' for {self.topic}.")
            return False

        # start = time.time()
        changed = self.__prs.reload_if_changed()
        if changed:
            self.recalculate_data(presentation=presentation, stage=stage)
            # logger.info(f'changed {time.time()-start:0.2f}s "{self.__ra.topic}"')
            logger.debug(f'plot: reload changed data: "{self.__ra.topic}"')
        return changed

    def recalculate_data(self, presentation, stage):
        x, y = presentation.get_xy(topic=self, stage=stage)
        assert len(x) == len(y)
        self.__plot_line.set_data(x, y)

    @classmethod
    def load(cls, dir_raw, plot_config,  presentations):
        assert isinstance(dir_raw, pathlib.Path)

        prs = PickleResultSummary.load(dir_raw)
        ra = ResultAttributes(dir_raw=dir_raw)
        return Topic(ra=ra, prs=prs, dir_raw=dir_raw, plot_config=plot_config, presentations=presentations)

    @property
    def topic(self) -> str:
        return self.__ra.topic

    @property
    def color_topic(self) -> str:
        return f"{self.color}-{self.topic}"

    def topic_basenoise(self, presentation) -> str:
        assert isinstance(presentation, Presentation)
        if presentation.supports_diff_basenoise:
            if self.basenoise:
                return f"{self.topic} - {Topic.TAG_BASENOISE}"
        return self.topic

    @property
    def color(self) -> str:
        return self.__ra.color

    @property
    def stages(self) -> list:
        l0 = [Stage(self, dict_stage) for dict_stage in self.__prs.dict_stages.values()]
        l0.sort(key=lambda stage: stage.stage)
        return l0

    def find_stage(self, stage):
        stage_100ms = 0.09
        if stage is None:
            for _stage in self.stages:
                if _stage.dt_s > stage_100ms:
                    return _stage
            __stage = self.stages[-1]
            msg = f"{str(self.dir_raw)}: No stage with dt_s {stage_100ms:0.5f}s. The latest stage has dt_s {__stage.dt_s:0.5f}s."
            raise Stage100msNotFoundException(msg)
            # logger.warning(f'topic {self.__ra.topic}: No stage with dt_s {stage_100ms:0.5f}s. Use the latest stage with dt_s {__stage.dt_s:0.5f}s instead.')
            # return __stage
        # This is a stage of another topic.
        # Find the corresponding stage of our topic
        for _stage in self.stages:
            if stage.stage == _stage.stage:
                return _stage
        return None

    def get_stepsize(self, stage):
        assert isinstance(stage, Stage)
        assert stage.belongs_to_topic(self)
        stepsize_bins_count = stage.stepsize_bins_count
        stepsize_bins_V = stage.stepsize_bins_V
        # Mask all array-elements with bins_count == 0
        # stepsize_bins_count = np.ma.masked_equal(stepsize_bins_count, 0)
        stepsize_bins_V = np.ma.masked_where(stepsize_bins_count == 0, stepsize_bins_V)
        stepsize_bins_count = np.ma.masked_where(stepsize_bins_count == 0, stepsize_bins_count)
        stepsize_bins_V = stepsize_bins_V.compressed()  # pylint: disable=no-member
        stepsize_bins_count = stepsize_bins_count.compressed()  # pylint: disable=no-member
        return (stepsize_bins_V, stepsize_bins_count)

    def get_timeserie(self, stage):
        assert isinstance(stage, Stage)
        assert stage.belongs_to_topic(self)
        # TODO(Hans): Cache this array
        x = np.linspace(start=0.0, stop=stage.dt_s * len(stage.samples_V), num=len(stage.samples_V))
        return (x, stage.samples_V)

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

    def _integral_index_start(self):
        fHz = self._plot_config.integral_index_start
        for i, f in enumerate(self.f):
            if fHz * 0.99 < f < fHz * 1.01:
                return i
        raise FrequencyNotFound(f"Frequency {fHz} not found")

    @property
    def f_INTEGRAL(self):
        return self.__prs.f[self._integral_index_start() :]

    @property
    def scaling_INTEGRAL(self):
        return np.sqrt(np.cumsum(self.scaling_PS[self._integral_index_start() :]))  # todo: start sum above frequency_complete_low_limit

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

        for (_f, value) in zip(f, v, strict=False):
            if is_border_decade(_f):
                if last_value is not None:
                    f_decade.append(_f)
                    value_decade.append(np.sqrt(value ** 2 - last_value ** 2))
                last_value = value
        return f_decade, value_decade

    def flickernoise(self):
        "return Vrms and comment"
        PS = self._presentations.dict["PS"].get_as_dict(self)

        f_low = 0.1
        f_high = 10.0
        P_sum = 0.0
        n = 0
        for f, p in zip(PS["x"], PS["y"], strict=False):
            if f > f_low * 1.001:
                P_sum += p
                n += 1
                if f > f_high * 0.999:
                    break

        flickernoise_minus_basenoise_Vrms = flickernoise_Vrms = math.sqrt(P_sum)
        comment = ""
        if n != 24:
            flickernoise_Vrms = 42.0
            comment = "Flickernoise: not enough values to calculate."

        if self.is_basenoise:
            # We are the basenoise
            flickernoise_minus_basenoise_Vrms = 0.0
        else:
            if self.basenoise is not None:
                assert not self.is_basenoise
                # A basenoise exists. Get the flickernoise and subtract
                _flickernoise_basenoise_Vrms, _dummy_Vrms, _comment = self.basenoise.flickernoise()
                flickernoise_minus_basenoise_Vrms = math.sqrt(max(0.0, flickernoise_Vrms ** 2 - _flickernoise_basenoise_Vrms ** 2))

        return flickernoise_Vrms, flickernoise_minus_basenoise_Vrms, comment


class ResizedArrays:
    """
    Given two curves (f/base_f and y/base_y).
    This class will find matching 'f' and remove all 'f' which are only in one of both curves.
    The resulting 'self.f', 'self.y', 'self.base_y' will have the same size.
    """

    def __init__(self, f, base_f, d, base_d):
        assert isinstance(f, list | tuple)
        assert isinstance(base_f, list | tuple)
        assert isinstance(d, list | tuple)
        assert isinstance(base_d, list | tuple)

        new_f = np.zeros(len(f), dtype=np.float32)
        new_d = np.zeros(len(f), dtype=np.float32)
        new_base_d = np.zeros(len(f), dtype=np.float32)

        idx = 0
        idx_base = 0
        idx_out = 0
        while True:
            if idx >= len(f):
                break
            if idx_base >= len(base_f):
                break
            diff = f[idx] - base_f[idx_base]
            if abs(diff) < 1e-12:
                # Both are equal
                new_f[idx_out] = f[idx]
                new_d[idx_out] = d[idx]
                new_base_d[idx_out] = base_d[idx_base]
                idx += 1
                idx_base += 1
                idx_out += 1
                continue
            if diff < 0:
                idx += 1
                continue
            idx_base += 1

        self.f = new_f[:idx_out]
        self.y = new_d[:idx_out]
        self.base_y = new_base_d[:idx_out]

        assert len(self.f) == len(self.y)
        assert len(self.f) == len(self.base_y)


class Presentation:
    def __init__(self, tag, supports_diff_basenoise, help_text, xy_func, x_label, y_label, logarithmic_scales=True):  # pylint: disable=too-many-arguments
        assert isinstance(tag, str)
        assert isinstance(supports_diff_basenoise, bool)
        assert isinstance(help_text, str)
        assert isinstance(xy_func, types.FunctionType)
        assert isinstance(y_label, str)
        assert isinstance(x_label, str)
        assert isinstance(logarithmic_scales, bool)
        self.tag = tag
        self.help_text = help_text
        self.__xy_func = xy_func
        self.supports_diff_basenoise = supports_diff_basenoise
        self.x_label = x_label
        self.y_label = y_label
        self.logarithmic_scales = logarithmic_scales

    def get_xy(self, topic, stage=None):
        assert isinstance(topic, Topic)
        assert isinstance(stage, None | Stage)
        if self.supports_diff_basenoise:
            if topic.basenoise:
                return self.__xy_func(topic.topic_minus_basenoise, stage)
        return self.__xy_func(topic, stage)

    def get_as_dict(self, topic):
        stage = None
        if self.requires_stage:
            stage = topic.find_stage(None)
        x, y = self.get_xy(topic=topic, stage=stage)
        return dict(  # noqa: C408
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

    @property
    def requires_stage(self):
        return self.tag in (PRESENTATION_STEPSIZE, PRESENTATION_TIMESERIE)


X_LABEL = "Frequency [Hz]"
DEFAULT_PRESENTATION = "LSD"
PRESENTATION_TIMESERIE = "TIMESERIE"
PRESENTATION_STEPSIZE = "STEPSIZE"


class Presentations:
    def __init__(self, plot_config: library_plot_config.PlotConfig):
        unit = plot_config.unit
        self.list = (
            Presentation(
                tag=DEFAULT_PRESENTATION,
                supports_diff_basenoise=True,
                x_label=X_LABEL,
                y_label=f"linear spectral density [{unit}/Hz^0.5]",
                help_text=f"linear spectral density [{unit}/Hz^0.5] represents the noise density. Useful to describe random noise.",
                xy_func=lambda topic, stage: (topic.f, topic.scaling_LSD),
            ),
            Presentation(
                tag="PSD",
                supports_diff_basenoise=True,
                x_label=X_LABEL,
                y_label=f"power spectral density [{unit}^2/Hz]",
                help_text=f"power spectral density [{unit}^2/Hz] ist just the square of the LSD. This representation of random noise is useful if you want to sum up the signal over a given frequency interval. ",
                xy_func=lambda topic, stage: (topic.f, topic.scaling_PSD)
            ),
            Presentation(
                tag="LS",
                supports_diff_basenoise=False, # Peter: abz Basenoise macht nicht viel Sinn weil LS typisch fuer eine Frequenz, z.B. 50 Hz gebraucht wird. Je nach Phasenlage ist das subtrahieren irrefuehrend. Daher nicht implementieren.
                x_label=X_LABEL,
                y_label=f"linear spectrum [{unit} rms]",
                help_text=f"linear spectrum [{unit} rms] represents the quantity in a frequency range. Useful if you want to measure the amplitude of a sinusoidal signal.",
                xy_func=lambda topic, stage: (topic.f, topic.scaling_LS)
            ),
            Presentation(
                tag="PS",
                supports_diff_basenoise=False,
                x_label=X_LABEL,
                y_label=f"power spectrum [{unit}^2]",
                help_text=f"power spectrum [{unit}^2] represents the square of LS. Useful if you want to measure the amplitude of a sinusoidal signal which is just between two frequency bins. You can now add the two values to get the amplitude of the sinusoidal signal.",
                xy_func=lambda topic, stage: (topic.f, topic.scaling_PS),
            ),
            Presentation(
                tag="INTEGRAL",
                supports_diff_basenoise=False,
                x_label=X_LABEL,
                y_label=f"integral [{unit} rms]",
                help_text=f"integral [{unit} rms] represents the integrated quantity from the lowest measured frequency up to the actual frequency. Example: Value at 1 kHz: is the quantity between 0.01 Hz and 1 kHz.",
                xy_func=lambda topic, stage: (topic.f_INTEGRAL, topic.scaling_INTEGRAL),
            ),
            Presentation(
                tag="DECADE",
                supports_diff_basenoise=False,
                x_label=X_LABEL,
                y_label=f"decade left of the point (noch falsch, nicht brauchen!) [{unit} rms]",
                help_text=f"decade left of the point (noch falsch, nicht brauchen!) [{unit} rms] Example: The value at 100 Hz represents the quantity between 100Hz/10 = 10 Hz and 100 Hz.",
                xy_func=lambda topic, stage: topic.decade_f_d
            ),
            Presentation(
                tag=PRESENTATION_STEPSIZE,
                supports_diff_basenoise=False,
                x_label=f"stepsize [{unit}]",
                y_label="count samples [samples/s]",
                help_text="TODO-PRESENTATION_STEPSIZE",
                xy_func=lambda topic, stage: topic.get_stepsize(stage)
            ),
            Presentation(
                tag=PRESENTATION_TIMESERIE,
                supports_diff_basenoise=False,
                x_label="timeserie [s]",
                y_label=f"sample [{unit}]",
                help_text="TODO-PRESENTATION_TIMESERIE",
                xy_func=lambda topic, stage: topic.get_timeserie(stage),
                logarithmic_scales=False
            ),
        )

        self.tags = [p.tag for p in self.list]
        self.dict = {p.tag: p for p in self.list}

    def get(self, tag):
        try:
            return self.dict[tag]
        except KeyError as e:
            raise Exception(f"Presentation {tag} not found! Choose one of {self.tags}.") from e

    def get_as_dict(self, topic):
        d = {}
        for p in self.list:
            try:
                d[p.tag] = p.get_as_dict(topic)
            except Stage100msNotFoundException as exc:
                logger.error(f"Presentation {p.tag}: {exc}")
        return d


def get_presentations(plot_config: library_plot_config.PlotConfig) -> Presentations:
    return Presentations(plot_config)

class StartupDuration:
    """
    Measure the duration during application startup
    to know where to optimize.
    """

    MAX_DURATION_S = 10

    def __init__(self):
        self.__on = True
        self.initialized_s = time.time()

    def log(self, msg):
        if self.__on:
            duration_s = time.time() - self.initialized_s
            logger.debug(f"time={duration_s:1.1f}: {msg}")

            if duration_s > StartupDuration.MAX_DURATION_S:
                self.__on = False
                logger.debug(f"time={duration_s:1.1f}: Switch off duration logging after {StartupDuration.MAX_DURATION_S:1.1f}s")

    def off(self):
        self.__on = False


class PlotDataMultipleDirectories:
    def __init__(self, topdir: pathlib.Path, plot_config: library_plot_config.PlotConfig, presentations: Presentations):
        assert isinstance(topdir, pathlib.Path)
        assert isinstance(plot_config, library_plot_config.PlotConfig)
        assert isinstance(presentations, Presentations)

        self.startup_duration = StartupDuration()
        self.startup_duration.log("PlotDataMultipleDirectories initialized")
        self.topdir = topdir
        self.topic_basenoise = None
        self.list_topics = []
        self.load_data(plot_config=plot_config, presentations=presentations)
        self.startup_duration.log("After load_data()")

    def load_data(self, plot_config: library_plot_config.PlotConfig, presentations: Presentations):
        self.topic_basenoise = None

        list_directories = self.read_directories()
        self.set_directories = {d.name for d in list_directories}

        for topic in self.list_topics:
            topic.basenoise = None

        list_topics_tmp = self.list_topics

        def topic_exists(dir_raw):
            for topic in list_topics_tmp:
                if topic.dir_raw == dir_raw:
                    return topic
            return None

        self.list_topics = []
        for dir_raw in list_directories:
            topic = topic_exists(dir_raw)
            if topic is None:
                topic = Topic.load(dir_raw=dir_raw, plot_config=plot_config,  presentations=presentations)
            self.list_topics.append(topic)

        self.list_topics.sort(key=lambda topic: topic.topic.upper())

        # Find topic with basenoise
        for topic in self.list_topics:
            if topic.is_basenoise:
                if self.topic_basenoise is not None:
                    raise Exception(f"More that one directory with '{Topic.TAG_BASENOISE}'")
                self.topic_basenoise = topic
                logger.info(f"Selected basenoise from '{topic.color_topic}'!")

        # Assign basenoise to all other topics
        if self.topic_basenoise:
            for topic in self.list_topics:
                if not topic.is_basenoise:
                    topic.set_basenoise(self.topic_basenoise)

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


class PlotDataSingleDirectory:
    def __init__(self, dir_raw, plot_config: library_plot_config.PlotConfig):
        assert isinstance(dir_raw, pathlib.Path)

        presentations=get_presentations(plot_config=plot_config)

        self.list_topics = [Topic.load(dir_raw=dir_raw, plot_config=plot_config, presentations=presentations)]
