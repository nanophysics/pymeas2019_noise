import pathlib

import config_plot
from pymeas2019_noise import library_gui, library_logger, library_plot, library_topic

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

library_logger.init_logger_gui(DIRECTORY_OF_THIS_FILE)


def run():
    plot_config = config_plot.get_plot_config()
    presentations = library_topic.get_presentations(plot_config=plot_config)

    plot_data = library_topic.PlotDataMultipleDirectories(
        topdir=DIRECTORY_OF_THIS_FILE,
        plot_config=plot_config,
        presentations=presentations,
    )

    plot_context = library_plot.PlotContext(
        plot_data=plot_data, plot_config=plot_config, presentations=presentations
    )
    plot_data.startup_duration.log("After PlotContext()")

    plot_data.startup_duration.log("After update_presentation()")

    app = library_gui.MyApp(plot_context=plot_context, presentations=presentations)
    plot_data.startup_duration.log("After MyApp()")
    app.MainLoop()


if __name__ == "__main__":
    run()
