import logging
import pathlib

import config_measurement
import config_plot
from .import library_logger, library_plot, library_topic

logger = logging.getLogger("logger")


def run(dir_measurement):
    library_logger.init_logger_composite_plots(dir_measurement)

    plot_config = config_plot.get_plot_config()
    presentations = library_topic.get_presentations(plot_config=plot_config)
    plot_data = library_topic.PlotDataMultipleDirectories(
        topdir=dir_measurement, plot_config=plot_config, presentations=presentations
    )
    plot_file = library_plot.PlotFile(
        plot_data=plot_data,
        plot_config=plot_config,
        presentations=presentations,
        write_files_directory=dir_measurement,
        title=config_measurement.TITLE,
    )
    plot_file.plot_presentations()

    try:
        import library_1_postprocess
    except ModuleNotFoundError:
        logger.error("No library_1_postprocess...")
        return
    logger.info(f"library_1_postprocess.postprocess({dir_measurement})")
    library_1_postprocess.postprocess(
        dir_measurement=dir_measurement, plot_data=plot_data
    )


if __name__ == "__main__":
    run(dir_measurement=pathlib.Path.cwd())
