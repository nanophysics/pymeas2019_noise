
# pylint: disable=import-error,no-name-in-module
import logging
import time
import warnings
from collections.abc import Callable
from typing import Any, cast

import matplotlib.animation
from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)

from . import library_plot

# Hide messages about experimental matplotlib tool API.
warnings.filterwarnings(action="ignore")

logger = logging.getLogger("logger")


class PlotPanel(QWidget):
    def __init__(self, plot_context: library_plot.PlotContext, parent: QWidget | None):
        super().__init__(parent)
        self._plot_context = plot_context
        self._plot_context: library_plot.PlotContext
        self.animation: matplotlib.animation.FuncAnimation | None = None
        self.canvas_last_resize_s: float | None = None

        self.canvas = FigureCanvasQTAgg(self._plot_context.fig)
        self.toolbar = NavigationToolbar2QTAgg(self.canvas, self)
        self.canvas.mpl_connect("resize_event", self._on_canvas_resize)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.toolbar, 0)
        self.setLayout(layout)

    def bind_mouse_motion(self, callback: Callable[[MouseEvent], None]) -> None:
        self.canvas.mpl_connect(
            "motion_notify_event",
            cast(Callable[[Any], Any], callback),
        )

    def _on_canvas_resize(self, _event: object) -> None:
        self.canvas_last_resize_s = time.monotonic()

    def init_plot_data(self) -> None:
        self.toolbar.update()

        self._plot_context.plot_data.startup_duration.log("FuncAnimation() - before")
        self.animation = matplotlib.animation.FuncAnimation(
            fig=self._plot_context.fig,
            func=cast(Callable[[Any], Any], self.animate),
            frames=None,
            interval=1000,
            init_func=None,
            repeat=False,
        )
        self._plot_context.plot_data.startup_duration.log("FuncAnimation() - after")

        self._plot_context.update_presentation()

    def animate(self, _frame: Any) -> None:
        """
        This will be called by a timer
        """
        if self.canvas_last_resize_s is not None:
            if self.canvas_last_resize_s + 0.5 < time.monotonic():
                logger.info("matplotlib-canvas: delayed resize")
                self.canvas.draw_idle()
                self.canvas_last_resize_s = None

        self._plot_context.animate()
