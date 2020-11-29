import pathlib

import library_path

library_path.find_append_path()

# pylint: disable=wrong-import-position
import library_topic
import library_plot
import library_logger
import config_measurement

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent


def run():
    library_logger.init_logger_composite_plots(DIRECTORY_OF_THIS_FILE)

    plotData = library_topic.PlotDataMultipleDirectories(DIRECTORY_OF_THIS_FILE)
    plotFile = library_plot.PlotFile(plotData=plotData, write_files_directory=DIRECTORY_OF_THIS_FILE, title=config_measurement.TITLE)
    plotFile.plot_presentations()


if __name__ == "__main__":
    run()
