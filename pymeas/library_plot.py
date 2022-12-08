"""
There are three modes:

do_show=False,do_animate=False: No GUI. Just write the plot into a file.
do_show=True,do_animate=False: GUI. Show the data, no animation.
do_show=True,do_animate=True: GUI. Show the data, animation.

"""
import sys
import logging
import pathlib
import subprocess

import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.animation

import run_0_measure

from . import library_plot_config
from . import library_topic

logger = logging.getLogger("logger")


class PlotContext:
    def __init__(self, plotData: library_topic.PlotDataMultipleDirectories, plot_config:library_plot_config.PlotConfig, presentations: library_topic.Presentations):
        assert isinstance(plotData, (library_topic.PlotDataSingleDirectory, library_topic.PlotDataMultipleDirectories))
        assert isinstance(plot_config, library_plot_config.PlotConfig)
        assert isinstance(presentations, library_topic.Presentations)
        self._plot_config = plot_config
        self._presentations = presentations
        # The currently active presentation
        self.__presentation = presentations.get(library_topic.DEFAULT_PRESENTATION)
        # The data to be displayed
        self.plotData = plotData
        self.__plot_is_invalid = True
        self.__topic = None
        self.__stage = None
        self.__fig, self.__ax = plt.subplots(figsize=(8, 4))

    @property
    def fig(self):
        return self.__fig

    @property
    def presentation_title(self):
        return self.__presentation.title

    @property
    def presentation_tag(self):
        return self.__presentation.tag

    def invalidate(self):
        self.__plot_is_invalid = True

    def set_presentation(self, presentation):
        assert isinstance(presentation, library_topic.Presentation)
        if self.__presentation != presentation:
            self.invalidate()
        self.__presentation = presentation

    def initialize_plot_lines(self):
        """
        Updates the plot: scales and lines
        """
        for topic in self.list_selected_topics:
            # Just a dummy plot line to be able to add axes and scale
            x = (0, 1)
            y = (0, 1)
            assert len(x) == len(y)
            (plot_line,) = self.__ax.plot(x, y, linestyle="none", linewidth=0.1, marker=".", markersize=3, color=topic.color, label=topic.topic_basenoise(self.__presentation))
            scale = "log" if self.__presentation.logarithmic_scales else "linear"
            self.__ax.set_xscale(scale)
            self.__ax.set_yscale(scale)
            topic.set_plot_line(plot_line)

        leg = self.__ax.legend(fancybox=True, framealpha=0.5)
        leg.get_frame().set_linewidth(0.0)

    def clear_figure(self):
        # for legend in self.__fig.legends:
        #     legend.remove()
        for line in self.__fig.lines:
            line.remove()
        # for axe in self.__fig.axes:
        #     axe.remove()
        while len(self.__ax.lines) > 0:
            # Why are the lines not removed in the first go?
            for line in self.__ax.lines:
                line.remove()

    def update_presentation(self):
        assert self.plotData is not None

        if self.__plot_is_invalid:
            self.__plot_is_invalid = False
            for topic in self.plotData.list_topics:
                topic.reset_plot_line()
            self.clear_figure()
            self.initialize_plot_lines()

        label_stepsize = set()

        for topic in self.list_selected_topics:
            stage = self.__stage
            if self.__presentation.requires_stage:
                stage = topic.find_stage(stage)
                if stage is None:
                    topic.remove_line()
                    logger.warning(f"No stage stored for topic {topic.color_topic}")
                    continue
                if stage is not None:
                    label_stepsize.add(stage.label)
            try:
                topic.recalculate_data(presentation=self.__presentation, stage=stage)
            except (library_topic.Stage100msNotFoundException, library_topic.FrequencyNotFound) as exc:
                logger.error(f"SKIPPED: Topic {topic.topic}: {exc}")
                continue

        x_label = self.__presentation.x_label
        if len(label_stepsize) > 0:
            x_label += "  "
            x_label += ", ".join(sorted(label_stepsize))
        plt.xlabel(x_label)
        plt.ylabel(self.__presentation.title)

        for ax in self.__fig.get_axes():
            ax.relim()
            ax.autoscale()
            plt.grid(True, which="major", axis="both", linestyle="-", color="gray", linewidth=0.5)
            plt.grid(True, which="minor", axis="both", linestyle="-", color="silver", linewidth=0.1)
            if self.__presentation.logarithmic_scales:
                ax.xaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10.0, numticks=20))
                ax.yaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10.0, numticks=20))
                # Uncomment to modify figure
                # self.__fig.set_size_inches(13.0, 7.0)
                #ax.set_xlim(1e-3, 1e4)
                #ax.set_ylim(1e-9, 1e-5)
                if self._plot_config.func_matplotlib_ax is not None:
                    if self.__presentation.tag != library_topic.PRESENTATION_STEPSIZE:
                        self._plot_config.func_matplotlib_ax(ax=ax)

        # The following line will take up to 5s. Why?
        # self.__fig.canvas.draw()

        if self.__presentation.logarithmic_scales:
            if self._plot_config.func_matplotlib_fig is not None:
                self._plot_config.func_matplotlib_fig(fig=self.__fig)


    @property
    def list_selected_topics(self) -> list:
        if self.__topic is None:
            return self.plotData.list_topics
        return [topic for topic in self.plotData.list_topics if self.__topic == topic]

    def animate(self):
        if self.plotData.directories_changed():
            logger.info("Directories changed: Reload all data!")
            self.invalidate()
            self.plotData.load_data(plot_config=self._plot_config, presentations=self._presentations)

        if self.__plot_is_invalid:
            self.update_presentation()
            return

        for topic in self.list_selected_topics:
            topic.reload_if_changed(presentation=self.__presentation, stage=self.__stage)

    def start_measurement(self, dir_raw):
        # The start button has been pressed
        # proc = subprocess.Popen(["cmd.exe", "/K", "start", sys.executable, run_0_measure.__file__, dir_raw])
        # proc = subprocess.Popen(["cmd.exe", "/K", "start", sys.executable, run_0_measure.__file__, dir_raw], start_new_session=True, startupinfo=subprocess.DETACHED_PROCESS)
        proc = subprocess.Popen([sys.executable, run_0_measure.__file__, dir_raw], creationflags=subprocess.CREATE_NEW_CONSOLE)  # pylint: disable=consider-using-with
        logger.info(f"Started measurement in folder '{dir_raw}' with pid={proc.pid}.")

    def open_directory_in_explorer(self):
        directory = pathlib.Path(run_0_measure.__file__).absolute().parent
        subprocess.Popen(["explorer", str(directory)])  # pylint: disable=consider-using-with

    @property
    def iter_topics(self):
        yield "all", None
        for topic in self.plotData.list_topics:
            yield topic.topic, topic

    def iter_stages(self, topic):
        assert isinstance(topic, (type(None), library_topic.Topic))
        if topic is None:
            # If topic is not defined. This may happen if ALL topics have been selected.
            # In this case, we return the stages of the first topic
            if len(self.plotData.list_topics) == 0:
                return
            _topic = self.plotData.list_topics[0]
            for stage in _topic.stages:
                yield stage.label, stage
            return

        for _topic in self.plotData.list_topics:
            if _topic.topic == topic.topic:
                for stage in _topic.stages:
                    yield stage.label, stage

    def select_topic_stage(self, presentation, topic, stage) -> None:
        assert isinstance(presentation, library_topic.Presentation)
        assert isinstance(topic, (type(None), library_topic.Topic))
        assert isinstance(stage, (type(None), library_topic.Stage))

        if self.__topic != topic:
            self.invalidate()
        if self.__stage != stage:
            self.invalidate()

        self.__topic = topic
        self.__stage = stage

        self.set_presentation(presentation=presentation)

    def open_display_clone(self):
        directory = pathlib.Path(run_0_measure.__file__).absolute().parent
        import run_0_plot_interactive

        subprocess.Popen([sys.executable, run_0_plot_interactive.__file__], cwd=directory)  # pylint: disable=consider-using-with

    def savefig(self, filename, dpi):
        self.__fig.savefig(filename, dpi=dpi)

    def close(self):
        self.__fig.clf()
        plt.close(self.__fig)
        plt.clf()
        plt.close()


class PlotFile:
    def __init__(self, plotData, plot_config: library_plot_config.PlotConfig, presentations: library_topic.Presentations, title=None, write_files=("png",), write_files_directory=None):
        assert isinstance(plot_config, library_plot_config.PlotConfig)
        assert isinstance(presentations, library_topic.Presentations)
        # Possible values: write_files=("png", "svg")
        self.plotData = plotData
        self._plot_config = plot_config
        self._presentations = presentations
        self.title = title
        self.write_files = write_files
        assert isinstance(write_files_directory, (type(None), pathlib.Path))
        if write_files_directory is None:
            # The current directory
            write_files_directory = pathlib.Path(__file__).absolute().parent
        self.write_files_directory = write_files_directory

    def plot_presentations(self):
        """
        Print all presentation (LSD, LS, PS, etc.)
        """
        for presentation in self._presentations.list:
            try:
                self.plot_presentation(presentation=presentation)
            except (library_topic.Stage100msNotFoundException, library_topic.FrequencyNotFound) as exc:
                logger.error(f"Presentation {presentation.tag}: {exc}")

    def plot_presentation(self, presentation):
        plot_context = PlotContext(plotData=self.plotData, plot_config=self._plot_config, presentations=self._presentations)
        try:
            if self.title:
                plt.title(self.title)

            plot_context.set_presentation(presentation=presentation)
            plot_context.update_presentation()

            for ext in self.write_files:
                filename = self.write_files_directory / f"result_{plot_context.presentation_tag}.{ext}"
                logger.info(filename)
                plot_context.savefig(filename=filename, dpi=300)

        finally:
            plot_context.close()
