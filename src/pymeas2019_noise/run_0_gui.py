import pathlib

import config_plot

from . import library_logger, library_plot, library_topic
from .qt_main import MyApp

directory_cwd = pathlib.Path.cwd()
library_logger.init_logger_gui(directory_cwd)


def run():
    plot_config = config_plot.get_plot_config()
    presentations = library_topic.get_presentations(plot_config=plot_config)

    plot_data = library_topic.PlotDataMultipleDirectories(
        topdir=directory_cwd,
        plot_config=plot_config,
        presentations=presentations,
    )

    plot_context = library_plot.PlotContext(
        plot_data=plot_data, plot_config=plot_config, presentations=presentations
    )
    plot_data.startup_duration.log("After PlotContext()")

    plot_data.startup_duration.log("After update_presentation()")

    app = MyApp(plot_context=plot_context, presentations=presentations)
    plot_data.startup_duration.log("After MyApp()")
    app.main_loop()


if __name__ == "__main__":
    run()
