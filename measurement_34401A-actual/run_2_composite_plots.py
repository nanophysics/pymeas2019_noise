import logging
import pathlib

# pylint: disable=wrong-import-position
import library_path

library_path.init(__file__)

from pymeas import library_logger, library_plot, library_topic

import config_measurement
import config_plot

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

logger = logging.getLogger("logger")


def run(dir_measurement):
    library_logger.init_logger_composite_plots(dir_measurement)

    plot_config = config_plot.get_plot_config()
    presentations = library_topic.get_presentations(plot_config=plot_config)
    plotData = library_topic.PlotDataMultipleDirectories(topdir=dir_measurement, plot_config=plot_config, presentations=presentations)
    plotFile = library_plot.PlotFile(plotData=plotData, plot_config=plot_config, presentations=presentations, write_files_directory=dir_measurement, title=config_measurement.TITLE)
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
