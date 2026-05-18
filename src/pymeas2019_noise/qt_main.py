from __future__ import annotations

# pylint: disable=import-error,no-name-in-module
import pathlib
import sys

from PySide6.QtWidgets import QApplication

import config_plot  # type: ignore[import-not-found]

from . import library_logger, library_plot, library_topic
from .qt_widget_main import MainWindow

directory_cwd = pathlib.Path.cwd()
library_logger.init_logger_gui(directory_cwd)


class MyApp:
    def __init__(
        self,
        plot_context: library_plot.PlotContext,
        presentations: library_topic.Presentations,
    ) -> None:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        assert isinstance(app, QApplication)
        self._qt_app = app
        self.window = MainWindow(
            plot_context=plot_context,
            presentations=presentations,
        )

    def main_loop(self) -> int:
        self.window.show()
        return self._qt_app.exec()
