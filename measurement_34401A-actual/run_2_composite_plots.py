import logging
import pathlib

import library_path

library_path.init(__file__)

# pylint: disable=wrong-import-position
from pymeas import library_topic
from pymeas import library_plot
from pymeas import library_logger

import config_measurement

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

logger = logging.getLogger("logger")


def run(dir_measurement):
    library_logger.init_logger_composite_plots(dir_measurement)

    plotData = library_topic.PlotDataMultipleDirectories(dir_measurement)
    plotFile = library_plot.PlotFile(plotData=plotData, write_files_directory=dir_measurement, title=config_measurement.TITLE)
    plotFile.plot_presentations()

    try:
        import library_1_postprocess
    except ModuleNotFoundError:
        logger.error("No library_1_postprocess...")
        return
    logger.info(f"library_1_postprocess.postprocess({dir_measurement})")
    library_1_postprocess.postprocess(dir_measurement=dir_measurement, plotData=plotData)


if __name__ == "__main__":
    run(DIRECTORY_OF_THIS_FILE)
