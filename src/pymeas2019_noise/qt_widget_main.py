from __future__ import annotations

# pylint: disable=import-error,no-name-in-module
import logging

from PySide6 import QtWidgets
from PySide6.QtCore import QTimer

from . import library_filelock, library_plot, library_topic
from .qt_widget_plot import PlotPanel
from .resources_compiled.gui_main import Ui_MainWindow

logger = logging.getLogger("logger")

FILELOCK_GUI = library_filelock.FilelockGui()

COLORS = (
    "blue",
    "orange",
    "black",
    "green",
    "red",
    "cyan",
    "magenta",
    "cornflowerblue",
    "navy",
    "purple",
    "lime",
    "red",
    "turquoise",
    "gold",
    "chocolate",
    "gray",
    "limegreen",
)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(
        self,
        plot_context: library_plot.PlotContext,
        presentations: library_topic.Presentations,
    ) -> None:
        super().__init__()
        self.setupUi(self)
        self._plot_context = plot_context
        self._presentations = presentations

        self.plotpanel = PlotPanel(self._plot_context, self.centralwidget)
        self.plotpanel.setObjectName("plot_panel")
        self.plotpanel.setContentsMargins(0, 0, 0, 0)

        self.statusbar.addWidget(QtWidgets.QLabel("Status", self.centralwidget))
        self.label_status_text = QtWidgets.QLabel("-", self.centralwidget)
        self.statusbar.addWidget(self.label_status_text, 1)

        self.verticalLayout_centralwidget.addWidget(self.plotpanel)

        self.setWindowTitle("pymeas2019_noise")
        self.resize(1400, 900)

        self._connect_signals()
        self._populate_widgets()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(2000)

        self.plotpanel.init_plot_data()

        self.on_button_reload_topic()

    def _connect_signals(self) -> None:
        self.button_start.clicked.connect(self.on_start)
        self.button_stop.clicked.connect(self.on_stop)
        self.button_skip_settle.clicked.connect(self.on_skip_settle)
        self.button_display_open_directory.clicked.connect(self.on_open_directory)
        self.button_display_clone.clicked.connect(self.on_display_clone)
        self.button_display_reload_topic.clicked.connect(self.on_button_reload_topic)
        self.button_display_reload_stage.clicked.connect(self.on_button_reload_stage)
        self.combo_box_presentation.currentIndexChanged.connect(
            self.on_combo_box_presentation
        )
        self.combo_box_display_topic.currentIndexChanged.connect(
            self.on_combo_box_display_topic
        )
        self.combo_box_display_stage.currentIndexChanged.connect(
            self.on_combo_box_display_stage
        )

    def _populate_widgets(self) -> None:
        for presentation in self._presentations.list:
            self.combo_box_presentation.addItem(presentation.title, presentation)

        idx = self.combo_box_presentation.findText(
            self._plot_context.presentation_title
        )
        if idx >= 0:
            self.combo_box_presentation.setCurrentIndex(idx)

        for color in COLORS:
            self.combo_box_measurement_color.addItem(color)
        self.combo_box_measurement_color.setCurrentIndex(0)

        self.text_ctrl_measurement_topic.setText(
            library_topic.ResultAttributes.getdatetime()
        )

    @property
    def presentation(self) -> library_topic.Presentation:
        presentation = self.combo_box_presentation.currentData()
        assert isinstance(presentation, library_topic.Presentation)
        return presentation

    @property
    def topic(self) -> library_topic.Topic | None:
        topic = self.combo_box_display_topic.currentData()
        if topic is None:
            return None
        assert isinstance(topic, library_topic.Topic)
        return topic

    @property
    def stage(self) -> library_topic.Stage | None:
        stage = self.combo_box_display_stage.currentData()
        if stage is None:
            return None
        assert isinstance(stage, library_topic.Stage)
        return stage

    def on_timer(self) -> None:
        is_measurement_running = FILELOCK_GUI.is_measurement_running()
        logger.debug(f"on_timer() is_measurement_running={is_measurement_running}")
        self.button_start.setEnabled(not is_measurement_running)
        self.button_stop.setEnabled(is_measurement_running)
        self.button_skip_settle.setEnabled(is_measurement_running)
        self.label_status_text.setText(FILELOCK_GUI.get_status())

    def on_start(self, _checked: bool = False) -> None:
        color = self.combo_box_measurement_color.currentText()
        topic = self.text_ctrl_measurement_topic.text().strip()
        dir_raw = f"{library_topic.DIRECTORY_NAME_RAW_PREFIX}{color}-{topic}"
        self._plot_context.start_measurement(dir_raw)

    def on_stop(self, _checked: bool = False) -> None:
        FILELOCK_GUI.stop_measurement_soft()

    def on_skip_settle(self, _checked: bool = False) -> None:
        FILELOCK_GUI.skip_settle()

    def on_combo_box_presentation(self, _index: int) -> None:
        logger.debug(f"on_combo_box_presentation(): {self.presentation.title}")
        self._plot_context.set_presentation(self.presentation)
        self._plot_context.update_presentation()
        self._enable_display_stage()

    def on_open_directory(self, _checked: bool = False) -> None:
        self._plot_context.open_directory_in_explorer()

    def on_display_clone(self, _checked: bool = False) -> None:
        self._plot_context.open_display_clone()

    def _enable_display_stage(self) -> None:
        enabled = self.presentation.requires_stage
        self.button_display_reload_stage.setEnabled(enabled)
        self.combo_box_display_stage.setEnabled(enabled)

    def on_button_reload_topic(self, _checked: bool = False) -> None:
        self.combo_box_display_topic.clear()
        for title, topic in self._plot_context.iter_topics:
            self.combo_box_display_topic.addItem(title, topic)

        if self.combo_box_display_topic.count() > 0:
            self.combo_box_display_topic.setCurrentIndex(0)
        self.on_button_reload_stage()

    def on_button_reload_stage(self, _checked: bool = False) -> None:
        self.combo_box_display_stage.clear()

        for title, stage in self._plot_context.iter_stages(self.topic):
            self.combo_box_display_stage.addItem(title, stage)

        if self.combo_box_display_stage.count() > 0:
            self.combo_box_display_stage.setCurrentIndex(0)

        self._enable_display_stage()

        self._plot_context.invalidate()
        self._plot_context.select_topic_stage(
            presentation=self.presentation,
            topic=self.topic,
            stage=self.stage,
        )

    def on_combo_box_display_topic(self, _index: int) -> None:
        self.on_button_reload_stage(False)
        self.on_combo_box_display_stage(0)

    def on_combo_box_display_stage(self, _index: int) -> None:
        self._plot_context.select_topic_stage(
            presentation=self.presentation,
            topic=self.topic,
            stage=self.stage,
        )
