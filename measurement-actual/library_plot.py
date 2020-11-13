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
    def __init__(self, plotData, fig, ax):
        # The currently active presentation
        self.presentation = None
        # The data to be displayed
        self.plotData = plotData
        self.fig = fig
        self.ax = ax

    def initialize_plot_lines(self):
        """
        Updates the plot: scales and lines
        """
        for topic in self.plotData.listTopics:
            x, y = self.presentation.get_xy(topic)
            assert len(x) == len(y)
            (plot_line,) = self.ax.plot(x, y, linestyle="none", linewidth=0.1, marker=".", markersize=3, color=topic.color, label=topic.topic)
            scale = "log" if self.presentation.logarithmic_scales else "linear"
            self.ax.set_xscale(scale)
            self.ax.set_yscale(scale)
            topic.set_plot_line(plot_line)

        leg = self.ax.legend(fancybox=True, framealpha=0.5)
        leg.get_frame().set_linewidth(0.0)

    def update_presentation(self, presentation=None, update=True):
        """
        If 'presentation' is given. Call 'initialize_plot_lines'.
        If 'update': Update the data in the graph
        """
        if presentation is not None:
            self.presentation = presentation
            if self.plotData is not None:
                # The presentation changed, update the graph
                self.plotData.remove_lines(fig=self.fig, ax=self.ax)
                self.initialize_plot_lines()

        if update:
            assert self.plotData is not None
            plt.xlabel(self.presentation.x_label)
            plt.ylabel(self.presentation.title)
            for topic in self.plotData.listTopics:
                topic.recalculate_data(presentation=self.presentation)
            for ax in self.fig.get_axes():
                ax.relim()
                ax.autoscale()
                plt.grid(True, which="major", axis="both", linestyle="-", color="gray", linewidth=0.5)
                plt.grid(True, which="minor", axis="both", linestyle="-", color="silver", linewidth=0.1)
                if self.presentation.logarithmic_scales:
                    ax.xaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10.0, numticks=20))
                    ax.yaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10.0, numticks=20))
                # Uncomment to modify figure
                # self.fig.set_size_inches(13.0, 7.0)
                # ax.set_xlim(1e-1, 1e4)
                # ax.set_ylim(1e-9, 1e-5)
            self.fig.canvas.draw()

    def animate(self):
        if self.plotData.directories_changed():
            self.plotData.remove_lines_and_reload_data(self.fig, self.ax)
            self.initialize_plot_lines()
            # initialize_grid()
            return

        for topic in self.plotData.listTopics:
            topic.reload_if_changed(self.presentation)

    def start_measurement(self, dir_raw):
        # The start button has been pressed
        # proc = subprocess.Popen(["cmd.exe", "/K", "start", sys.executable, run_0_measure.__file__, dir_raw])
        proc = subprocess.Popen(["cmd.exe", "/K", "start", sys.executable, run_0_measure.__file__, dir_raw], start_new_session=True)
        logger.info(f"Started measurement in folder '{dir_raw}' with pid={proc.pid}.")

    def open_directory_in_explorer(self):
        directory = pathlib.Path(run_0_measure.__file__).absolute().parent
        subprocess.Popen(["explorer", str(directory)])

    def open_display_clone(self):
        directory = pathlib.Path(run_0_measure.__file__).absolute().parent
        import run_0_plot_interactive

        subprocess.Popen([sys.executable, run_0_plot_interactive.__file__], cwd=directory)


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
        for tag in library_topic.PRESENTATIONS.tags:
            self.plot_presentation(presentation_tag=tag)

    def plot_presentation(self, presentation_tag=library_topic.DEFAULT_PRESENTATION):
        fig, ax = plt.subplots(figsize=(8, 4))
        plot_context = PlotContext(plotData=self.plotData, fig=fig, ax=ax)
        plot_context.update_presentation(library_topic.PRESENTATIONS.get(presentation_tag), update=False)

        if self.title:
            plt.title(self.title)

        plot_context.initialize_plot_lines()
        plot_context.update_presentation()

        for ext in self.write_files:
            filename = self.write_files_directory / f"result_{plot_context.presentation.tag}.{ext}"
            logger.info(filename)
            fig.savefig(filename, dpi=300)

        fig.clf()
        plt.close(fig)
        plt.clf()
        plt.close()
