"""
This code is base on a sample from
  Copyright (C) 2003-2004 Andrew Straw, Jeremy O'Donoghue and others

  License: This work is licensed under the PSF. A copy should be included
  with this source code, and is also available at
  https://docs.python.org/3/license.html
"""
import time
import logging
import pathlib
import itertools

import warnings

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg
import matplotlib.animation

import wx
import wx.xrc as xrc

from . import library_filelock
from . import library_topic

# Hide messages like:
#   Treat the new Tool classes introduced in v1.5 as experimental for now, the API will likely change in version 2.1 and perhaps the rcParam as well
warnings.filterwarnings(action="ignore")

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
)


class Duration:
    def __init__(self, title):
        self._title = title
        self._start_s = time.time()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        logger.debug(f"{self._title} {time.time() - self._start_s:0.3f}s")


def log_duration(f):
    def new_f(*args, **vargs):
        start_s = time.time()
        f(*args, **vargs)
        logger.debug(f"{f.__name__}(): {time.time() - start_s:0.3f}s")

    return new_f


class PlotPanel(wx.Panel):
    def __init__(self, parent, app):
        self._app = app
        self._plot_context = app._plot_context
        self.animation = None
        self.canvas_force_resize = False
        self.canvas_last_resize_s = None

        wx.Panel.__init__(self, parent, -1)

        self.canvas = FigureCanvasWxAgg(self, -1, self._plot_context.fig)
        self.toolbar = NavigationToolbar2WxAgg(self.canvas)  # matplotlib toolbar
        self.toolbar.Realize()

        self.canvas.Bind(wx.EVT_SIZE, self.OnSizeCanvas)

        # Now put all into a sizer which will resize the figure when the window size changes
        sizer = wx.BoxSizer(wx.VERTICAL)
        # This way of adding to sizer allows resizing
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        # Best to allow the toolbar to resize!
        sizer.Add(self.toolbar, 0, wx.GROW)
        self.SetSizer(sizer)
        self.Fit()

    def OnSizeCanvas(self, event):
        logger.debug(f'_on_size_canvas {event.GetSize()}')
        self.canvas_last_resize_s = time.time()
        if self.canvas_force_resize:
            event.Skip()

    def init_plot_data(self):
        self.toolbar.update()  # Not sure why this is needed - ADS

        def endless_iter():
            yield from itertools.count(start=42)

        self._plot_context.plotData.startup_duration.log("FuncAnimation() - before")
        self.animation = matplotlib.animation.FuncAnimation(
            fig=self._plot_context.fig,
            func=self.animate,
            frames=endless_iter(),
            # Delay between frames in milliseconds
            interval=1000,
            # A function used to draw a clear frame. If not given, the results of drawing from the first item in the frames sequence will be used.
            init_func=None,
            repeat=False,
        )
        self._plot_context.plotData.startup_duration.log("FuncAnimation() - after")

        # Important: If this statement is BEFORE 'FuncAnimation', the animation sometimes does not start!
        with Duration("update_presentation():") as elapsed:
            self._plot_context.update_presentation()

    def GetToolBar(self):
        # You will need to override GetToolBar if you are using an
        # unmanaged toolbar in your frame
        return self.toolbar

    @log_duration
    def animate(self, i):
        self._plot_context.plotData.startup_duration.log("animate() - beginning")

        if self.canvas_last_resize_s:
            # The frame has been resized
            if self.canvas_last_resize_s + 0.5 < time.time():
                # And the last event was more than 500ms ago
                logger.info('matplotlib-canvas: delayed resize')
                # self.canvas.SetSize(self.canvas_requested_size)
                self.canvas_force_resize = True
                self.Layout()
                self.canvas_force_resize = False
                self.canvas_last_resize_s = None

        self._plot_context.animate()

class MyApp(wx.App):  # pylint: disable=too-many-instance-attributes
    def __init__(self, plot_context):
        self._plot_context = plot_context
        self.res = None
        self.frame = None
        self.panel = None
        self.plotpanel = None
        self.button_start = None
        self.button_stop = None
        self.button_display_open_directory = None
        self.button_display_clone = None
        self.combo_box_measurement_color = None
        self.text_ctrl_measurement_topic = None
        self.label_status_text = None
        self.label_coordinates = None
        self.button_display_reload_topic = None
        self.button_display_reload_stage = None
        self.combo_box_display_topic = None
        self.combo_box_display_stage = None
        self.combo_box_presentation = None
        self.timer = None

        wx.App.__init__(self)

    def OnInit(self):  # pylint: disable=too-many-statements
        self._plot_context.plotData.startup_duration.log("OnInit() - beginning")

        xrcfile = pathlib.Path(__file__).absolute().with_suffix(".xrc")
        logger.debug(f"Load {xrcfile}")
        self.res = xrc.XmlResource(str(xrcfile))

        # main frame and panel ---------

        self.frame = self.res.LoadFrame(None, "MainFrame")
        self.panel = xrc.XRCCTRL(self.frame, "MainPanel")

        # matplotlib panel -------------

        # container for matplotlib panel (I like to make a container
        # panel for our panel so I know where it'll go when in XRCed.)
        plot_container = xrc.XRCCTRL(self.frame, "plot_container_panel")
        sizer = wx.BoxSizer(wx.VERTICAL)

        # matplotlib panel itself
        self.plotpanel = PlotPanel(plot_container, self)

        # wx boilerplate
        sizer.Add(self.plotpanel, 1, wx.EXPAND)
        plot_container.SetSizer(sizer)

        # buttons ------------------
        self.button_start = xrc.XRCCTRL(self.frame, "button_measurement_start")
        self.button_start.Bind(wx.EVT_BUTTON, self.OnStart)
        self.button_stop = xrc.XRCCTRL(self.frame, "button_measurement_stop")
        self.button_stop.Bind(wx.EVT_BUTTON, self.OnStop)
        button_measurement_skip_settle = xrc.XRCCTRL(self.frame, "button_measurement_skip_settle")
        button_measurement_skip_settle.Bind(wx.EVT_BUTTON, self.OnSkipSettle)
        self.button_display_open_directory = xrc.XRCCTRL(self.frame, "button_display_open_directory")
        self.button_display_open_directory.Bind(wx.EVT_BUTTON, self.OnOpenDirectory)
        self.button_display_clone = xrc.XRCCTRL(self.frame, "button_display_clone")
        self.button_display_clone.Bind(wx.EVT_BUTTON, self.OnDisplayClone)

        # display select topic/stage
        self.button_display_reload_topic = xrc.XRCCTRL(self.frame, "button_display_reload_topic")
        self.button_display_reload_topic.Bind(wx.EVT_BUTTON, self.OnButtonReloadTopic)
        self.button_display_reload_stage = xrc.XRCCTRL(self.frame, "button_display_reload_stage")
        self.button_display_reload_stage.Bind(wx.EVT_BUTTON, self.OnButtonReloadStage)
        self.combo_box_display_topic = xrc.XRCCTRL(self.frame, "combo_box_display_topic")
        self.combo_box_display_topic.Bind(wx.EVT_COMBOBOX, self.OnComboBoxDisplayTopic)
        self.combo_box_display_stage = xrc.XRCCTRL(self.frame, "combo_box_display_stage")
        self.combo_box_display_stage.Bind(wx.EVT_COMBOBOX, self.OnComboBoxDisplayStage)

        # presentation combo ------------------
        self.combo_box_presentation = xrc.XRCCTRL(self.frame, "combo_box_presentation")
        self.combo_box_presentation.Bind(wx.EVT_COMBOBOX, self.OnComboBoxPresentation)
        for presentation in library_topic.PRESENTATIONS.list:
            self.combo_box_presentation.Append(presentation.title, presentation)

        idx = self.combo_box_presentation.FindString(self._plot_context.presentation_title)
        self.combo_box_presentation.Select(idx)

        self.combo_box_measurement_color = xrc.XRCCTRL(self.frame, "combo_box_measurement_color")
        self.combo_box_measurement_color.Append(COLORS)
        self.combo_box_measurement_color.Select(0)

        self.text_ctrl_measurement_topic = xrc.XRCCTRL(self.frame, "text_ctrl_measurement_topic")
        self.text_ctrl_measurement_topic.Value = library_topic.ResultAttributes.getdatetime()

        self.label_status_text = xrc.XRCCTRL(self.frame, "label_status_text")
        font = self.label_status_text.GetFont()
        font.Weight = wx.BOLD  # pylint: disable=no-member
        self.label_status_text.SetFont(font)

        self.label_coordinates = xrc.XRCCTRL(self.frame, "label_coordinates")
        self.plotpanel.canvas.mpl_connect("motion_notify_event", self.UpdateStatusBar)

        # final setup ------------------
        self.frame.Show()

        self.SetTopWindow(self.frame)

        self.plotpanel.init_plot_data()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(1000)  # 1 second interval

        self.OnButtonReloadTopic(event=None)

        self._plot_context.plotData.startup_duration.log("OnInit() - done")
        return True

    def OnTimer(self, event):
        # do whatever you want to do every second here

        is_measurement_running = FILELOCK_GUI.is_measurement_running()
        logger.debug(f"OnTimer() is_measurement_running={is_measurement_running}")
        self.button_start.Enabled = not is_measurement_running
        self.button_stop.Enabled = is_measurement_running

        self.label_status_text.SetLabel(FILELOCK_GUI.get_status())

    def OnStart(self, event):
        dir_raw = f"{library_topic.DIRECTORY_NAME_RAW_PREFIX}{self.combo_box_measurement_color.Value}-{self.text_ctrl_measurement_topic.Value}"

        self._plot_context.start_measurement(dir_raw)

    def OnStop(self, event):
        FILELOCK_GUI.stop_measurement_soft()

    def OnSkipSettle(self, event):
        FILELOCK_GUI.skip_settle()

    def OnComboBoxPresentation(self, event):
        logger.debug(f'OnComboBoxPresentation(): {self.presentation.title}')
        self._plot_context.set_presentation(self.presentation)
        self._plot_context.update_presentation()
        self.__enable_display_stage()

    def UpdateStatusBar(self, event):
        if event.inaxes:
            self.label_coordinates.SetLabel(f"x={event.xdata:e}  y={event.ydata:e}")

    def OnOpenDirectory(self, event):
        self._plot_context.open_directory_in_explorer()

    def OnDisplayClone(self, event):
        self._plot_context.open_display_clone()

    @property
    def presentation(self):
        return self.combo_box_presentation.GetClientData(self.combo_box_presentation.Selection)

    @property
    def topic(self):
        return self.combo_box_display_topic.GetClientData(self.combo_box_display_topic.Selection)

    @property
    def stage(self):
        selection = self.combo_box_display_stage.Selection
        if selection == -1:
            return None
        return self.combo_box_display_stage.GetClientData(selection)

    @property
    def is_presentation_timeseries(self):
        return self.presentation.tag == library_topic.PRESENTATION_TIMESERIE

    def __enable_display_stage(self):
        enabled = False
        if self.is_presentation_timeseries:
            enabled = self.topic is not None
        assert isinstance(enabled, bool)
        self.button_display_reload_stage.Enabled = enabled
        self.combo_box_display_stage.Enabled = enabled

    def OnButtonReloadTopic(self, event):
        self.combo_box_display_topic.Clear()
        for title, topic in self._plot_context.iter_topics:
            self.combo_box_display_topic.Append(title, topic)
        self.combo_box_display_topic.Select(0)

        self.OnButtonReloadStage(event=None)

    def OnButtonReloadStage(self, event):
        self.combo_box_display_stage.Clear()

        for title, stage in self._plot_context.iter_stages(self.topic):
            self.combo_box_display_stage.Append(title, stage)

        self.combo_box_display_stage.Select(0)

        self.__enable_display_stage()

        self._plot_context.invalidate()
        self._plot_context.select_topic_stage(presentation=self.presentation, topic=self.topic, stage=self.stage)

    def OnComboBoxDisplayTopic(self, event):
        # Update the combobox
        self.OnButtonReloadStage(event=None)
        # Update the diagram
        self.OnComboBoxDisplayStage(event=None)

    def OnComboBoxDisplayStage(self, event):
        self._plot_context.select_topic_stage(presentation=self.presentation, topic=self.topic, stage=self.stage)
