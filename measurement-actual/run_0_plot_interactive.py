import pathlib

import library_path

library_path.find_append_path()

# pylint: disable=wrong-import-position
from pymeas import library_topic
from pymeas import library_plot
from pymeas import library_gui
from pymeas import library_logger

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

library_logger.init_logger_gui(DIRECTORY_OF_THIS_FILE)


def run():
    plotData = library_topic.PlotDataMultipleDirectories(DIRECTORY_OF_THIS_FILE)

    plot_context = library_plot.PlotContext(plotData=plotData)
    plotData.startup_duration.log("After PlotContext()")

    plotData.startup_duration.log("After update_presentation()")

    app = library_gui.MyApp(plot_context)
    plotData.startup_duration.log("After MyApp()")
    app.MainLoop()


if __name__ == "__main__":
    run()
