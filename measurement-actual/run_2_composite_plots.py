import pathlib

import library_topic
import library_plot
import library_path
import config_measurement

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent


def run():
    library_path.init_logger_condense()

    plotData = library_topic.PlotDataMultipleDirectories(DIRECTORY_OF_THIS_FILE)
    plotFile = library_plot.PlotFile(plotData=plotData, title=config_measurement.TITLE)
    plotFile.plot_presentations()


if __name__ == "__main__":
    run()
