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

import library_topic
import run_0_measure

logger = logging.getLogger("logger")


class PlotContext:
    def __init__(self, plotData):
        # The currently active presentation
        self.__presentation = library_topic.PRESENTATIONS.get(library_topic.DEFAULT_PRESENTATION)
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
            x, y = self.__presentation.get_xy(topic=topic, stage=self.__stage)
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

        plt.xlabel(self.__presentation.x_label)
        plt.ylabel(self.__presentation.title)

        for topic in self.list_selected_topics:
            topic.recalculate_data(presentation=self.__presentation, stage=self.__stage)

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
            # ax.set_xlim(1e-1, 1e4)
            # ax.set_ylim(1e-9, 1e-5)

        # The following line will take up to 5s. Why?
        # self.__fig.canvas.draw()

    @property
    def list_selected_topics(self) -> list:
        if self.__topic is None:
            return self.plotData.list_topics
        return [topic for topic in self.plotData.list_topics if self.__topic == topic]

    def animate(self):
        if self.plotData.directories_changed():
            self.invalidate()
            self.plotData.load_data()

        if self.__plot_is_invalid:
            self.update_presentation()
            return

        for topic in self.list_selected_topics:
            topic.reload_if_changed(presentation=self.__presentation, stage=self.__stage)


    def start_measurement(self, dir_raw):
        # The start button has been pressed
        # proc = subprocess.Popen(["cmd.exe", "/K", "start", sys.executable, run_0_measure.__file__, dir_raw])
        # proc = subprocess.Popen(["cmd.exe", "/K", "start", sys.executable, run_0_measure.__file__, dir_raw], start_new_session=True, startupinfo=subprocess.DETACHED_PROCESS)
        proc = subprocess.Popen([sys.executable, run_0_measure.__file__, dir_raw], creationflags=subprocess.CREATE_NEW_CONSOLE)
        logger.info(f"Started measurement in folder '{dir_raw}' with pid={proc.pid}.")

    def open_directory_in_explorer(self):
        directory = pathlib.Path(run_0_measure.__file__).absolute().parent
        subprocess.Popen(["explorer", str(directory)])

    @property
    def iter_topics(self):
        yield "all", None
        for topic in self.plotData.list_topics:
            yield topic.topic, topic

    def iter_stages(self, topic):
        assert isinstance(topic, (type(None), library_topic.Topic))
        if topic is None:
            yield "-", None
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

        subprocess.Popen([sys.executable, run_0_plot_interactive.__file__], cwd=directory)

    def savefig(self, filename, dpi):
        self.__fig.savefig(filename, dpi=dpi)

    def close(self):
        self.__fig.clf()
        plt.close(self.__fig)
        plt.clf()
        plt.close()


class PlotFile:
    def __init__(self, plotData, title=None, write_files=("png",), write_files_directory=None):
        """
        Possible values: write_files=("png", "svg")
        """
        self.plotData = plotData
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
        for presentation in library_topic.PRESENTATIONS.list:
            if presentation.tag == library_topic.PRESENTATION_TIMESERIE:
                continue
            self.plot_presentation(presentation=presentation)

    def plot_presentation(self, presentation):
        plot_context = PlotContext(plotData=self.plotData)

        if self.title:
            plt.title(self.title)

        plot_context.set_presentation(presentation=presentation)
        plot_context.update_presentation()

        for ext in self.write_files:
            filename = self.write_files_directory / f"result_{plot_context.presentation_tag}.{ext}"
            logger.info(filename)
            plot_context.savefig(filename=filename, dpi=300)

        plot_context.close()
