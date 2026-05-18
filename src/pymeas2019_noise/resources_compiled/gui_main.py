################################################################################
## Form generated from reading UI file 'gui_main.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QMetaObject,
    QRect,
)
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1020, 809)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_centralwidget = QVBoxLayout(self.centralwidget)
        self.verticalLayout_centralwidget.setSpacing(3)
        self.verticalLayout_centralwidget.setObjectName("verticalLayout_centralwidget")
        self.verticalLayout_centralwidget.setSizeConstraint(
            QLayout.SizeConstraint.SetMaximumSize
        )
        self.verticalLayout_centralwidget.setContentsMargins(0, 0, 0, 0)
        self.group_measurement = QGroupBox(self.centralwidget)
        self.group_measurement.setObjectName("group_measurement")
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.group_measurement.sizePolicy().hasHeightForWidth()
        )
        self.group_measurement.setSizePolicy(sizePolicy)
        self.group_measurement.setFlat(True)
        self.group_measurement.setCheckable(False)
        self.horizontalLayout = QHBoxLayout(self.group_measurement)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(3, 0, 3, 0)
        self.combo_box_measurement_color = QComboBox(self.group_measurement)
        self.combo_box_measurement_color.setObjectName("combo_box_measurement_color")

        self.horizontalLayout.addWidget(self.combo_box_measurement_color)

        self.text_ctrl_measurement_topic = QLineEdit(self.group_measurement)
        self.text_ctrl_measurement_topic.setObjectName("text_ctrl_measurement_topic")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.text_ctrl_measurement_topic.sizePolicy().hasHeightForWidth()
        )
        self.text_ctrl_measurement_topic.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.text_ctrl_measurement_topic)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.button_start = QPushButton(self.group_measurement)
        self.button_start.setObjectName("button_start")

        self.horizontalLayout.addWidget(self.button_start)

        self.button_skip_settle = QPushButton(self.group_measurement)
        self.button_skip_settle.setObjectName("button_skip_settle")

        self.horizontalLayout.addWidget(self.button_skip_settle)

        self.button_stop = QPushButton(self.group_measurement)
        self.button_stop.setObjectName("button_stop")

        self.horizontalLayout.addWidget(self.button_stop)

        self.verticalLayout_centralwidget.addWidget(self.group_measurement)

        self.group_display = QGroupBox(self.centralwidget)
        self.group_display.setObjectName("group_display")
        self.horizontalLayout_3 = QHBoxLayout(self.group_display)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(3, 0, 3, 0)
        self.combo_box_presentation = QComboBox(self.group_display)
        self.combo_box_presentation.setObjectName("combo_box_presentation")

        self.horizontalLayout_3.addWidget(self.combo_box_presentation)

        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.button_display_reload_topic = QPushButton(self.group_display)
        self.button_display_reload_topic.setObjectName("button_display_reload_topic")

        self.horizontalLayout_3.addWidget(self.button_display_reload_topic)

        self.combo_box_display_topic = QComboBox(self.group_display)
        self.combo_box_display_topic.setObjectName("combo_box_display_topic")

        self.horizontalLayout_3.addWidget(self.combo_box_display_topic)

        self.button_display_reload_stage = QPushButton(self.group_display)
        self.button_display_reload_stage.setObjectName("button_display_reload_stage")

        self.horizontalLayout_3.addWidget(self.button_display_reload_stage)

        self.combo_box_display_stage = QComboBox(self.group_display)
        self.combo_box_display_stage.setObjectName("combo_box_display_stage")

        self.horizontalLayout_3.addWidget(self.combo_box_display_stage)

        self.horizontalSpacer_3 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.button_display_open_directory = QPushButton(self.group_display)
        self.button_display_open_directory.setObjectName(
            "button_display_open_directory"
        )

        self.horizontalLayout_3.addWidget(self.button_display_open_directory)

        self.button_display_clone = QPushButton(self.group_display)
        self.button_display_clone.setObjectName("button_display_clone")

        self.horizontalLayout_3.addWidget(self.button_display_clone)

        self.verticalLayout_centralwidget.addWidget(self.group_display)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1020, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "MainWindow", None)
        )
        self.group_measurement.setTitle(
            QCoreApplication.translate("MainWindow", "Measurement", None)
        )
        self.button_start.setText(
            QCoreApplication.translate("MainWindow", "Start", None)
        )
        self.button_skip_settle.setText(
            QCoreApplication.translate("MainWindow", "Skip Settle", None)
        )
        self.button_stop.setText(QCoreApplication.translate("MainWindow", "Stop", None))
        self.group_display.setTitle(
            QCoreApplication.translate("MainWindow", "Display", None)
        )
        self.button_display_reload_topic.setText(
            QCoreApplication.translate("MainWindow", "Reload Topic", None)
        )
        self.button_display_reload_stage.setText(
            QCoreApplication.translate("MainWindow", "Reload Stage", None)
        )
        self.button_display_open_directory.setText(
            QCoreApplication.translate("MainWindow", "Open Directory", None)
        )
        self.button_display_clone.setText(
            QCoreApplication.translate("MainWindow", "Clone This Display", None)
        )

    # retranslateUi
