import pathlib

import library_path

library_path.find_append_path()

# pylint: disable=wrong-import-position
from pymeas import library_topic
from pymeas import library_plot
from pymeas import library_logger

import config_measurement

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent


def run(dir_measurement):
    library_logger.init_logger_composite_plots(dir_measurement)

    plotData = library_topic.PlotDataMultipleDirectories(dir_measurement)
    plotFile = library_plot.PlotFile(plotData=plotData, write_files_directory=dir_measurement, title=config_measurement.TITLE)
    plotFile.plot_presentations()


if __name__ == "__main__":
    run(DIRECTORY_OF_THIS_FILE)
