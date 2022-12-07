import pathlib

# pylint: disable=wrong-import-position
import library_path

library_path.init(__file__)

import config_plot

from pymeas import library_topic
from pymeas import library_plot
from pymeas import library_gui
from pymeas import library_logger

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

library_logger.init_logger_gui(DIRECTORY_OF_THIS_FILE)


def run():
    plot_config = config_plot.get_plot_config()
    presentations = library_topic.get_presentations(plot_config=plot_config)

    plotData = library_topic.PlotDataMultipleDirectories(topdir=DIRECTORY_OF_THIS_FILE, plot_config=plot_config, presentations=presentations)

    plot_context = library_plot.PlotContext(plotData=plotData, plot_config=plot_config, presentations=presentations)
    plotData.startup_duration.log("After PlotContext()")

    plotData.startup_duration.log("After update_presentation()")

    app = library_gui.MyApp(plot_context=plot_context, presentations=presentations)
    plotData.startup_duration.log("After MyApp()")
    app.MainLoop()


if __name__ == "__main__":
    run()
