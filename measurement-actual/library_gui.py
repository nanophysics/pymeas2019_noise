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

import library_filelock
import library_topic

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

    @property
    def duration(self):
        duration_s = time.time() - self._start_s
        return f"{duration_s:0.2f}s"

    def __enter__(self):
        logger.debug(f"{self._title} START")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        logger.debug(f"{self._title} END {self.duration}")


class PlotPanel(wx.Panel):
    def __init__(self, parent, app):
        self._app = app
        self._plot_context = app._plot_context

        wx.Panel.__init__(self, parent, -1)

        self.canvas = FigureCanvasWxAgg(self, -1, self._plot_context.fig)
        self.toolbar = NavigationToolbar2WxAgg(self.canvas)  # matplotlib toolbar
        self.toolbar.Realize()

        # Now put all into a sizer which will resize the figure when the window size changes
        sizer = wx.BoxSizer(wx.VERTICAL)
        # This way of adding to sizer allows resizing
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        # Best to allow the toolbar to resize!
        sizer.Add(self.toolbar, 0, wx.GROW)
        self.SetSizer(sizer)
        self.Fit()

    def init_plot_data(self):
        self._plot_context.update_presentation()

        if True:

            self._plot_context.animation = matplotlib.animation.FuncAnimation(
                fig=self._plot_context.fig,
                func=self.animate,
                frames=self.endless_iter(),
                # Delay between frames in milliseconds
                interval=2000,
                # A function used to draw a clear frame. If not given, the results of drawing from the first item in the frames sequence will be used.
                init_func=None,
                repeat=False,
            )

        self.toolbar.update()  # Not sure why this is needed - ADS

    def GetToolBar(self):
        # You will need to override GetToolBar if you are using an
        # unmanaged toolbar in your frame
        return self.toolbar

    def OnStart(self, event):
        # self._app.button_start.Enabled = False
        # self._app.button_stop.Enabled = True

        dir_raw = f"{library_topic.DIRECTORY_NAME_RAW_PREFIX}{self._app.combo_box_measurement_color.Value}-{self._app.text_ctrl_measurement_topic.Value}"

        self._plot_context.start_measurement(dir_raw)

    def OnStop(self, event):
        # self._plot_context.animation = None
        # self._app.button_start.Enabled = True
        # self._app.button_stop.Enabled = False
        FILELOCK_GUI.stop_measurement_soft()

    def OnComboBoxPresentation(self, event):
        combobox = event.EventObject
        presentation = combobox.GetClientData(combobox.Selection)
        self._plot_context.update_presentation(presentation=presentation, update=True)
        logger.debug(presentation.title)

    def endless_iter(self):
        yield from itertools.count(start=42)

    def animate(self, i):
        with Duration("animate") as elapsed:
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
        self.button_restart = None
        self.button_display_open_directory = None
        self.button_display_clone = None
        self.combo_box_measurement_color = None
        self.text_ctrl_measurement_topic = None
        self.label_coordinates = None
        self.timer = None

        wx.App.__init__(self)

    def OnInit(self):
        xrcfile = pathlib.Path(__file__).absolute().with_suffix(".xrc")
        logger.debug(f'Load {xrcfile}')
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
        self.button_start.Bind(wx.EVT_BUTTON, self.plotpanel.OnStart)
        self.button_stop = xrc.XRCCTRL(self.frame, "button_measurement_stop")
        self.button_stop.Bind(wx.EVT_BUTTON, self.plotpanel.OnStop)
        self.button_restart = xrc.XRCCTRL(self.frame, "button_measurement_restart")
        self.button_restart.Bind(wx.EVT_BUTTON, self.OnRestart)
        self.button_display_open_directory = xrc.XRCCTRL(self.frame, "button_display_open_directory")
        self.button_display_open_directory.Bind(wx.EVT_BUTTON, self.OnOpenDirectory)
        self.button_display_clone = xrc.XRCCTRL(self.frame, "button_display_clone")
        self.button_display_clone.Bind(wx.EVT_BUTTON, self.OnDisplayClone)

        # presentation combo ------------------
        combo_box_presentation = xrc.XRCCTRL(self.frame, "combo_box_presentation")
        combo_box_presentation.Bind(wx.EVT_COMBOBOX, self.plotpanel.OnComboBoxPresentation)
        for presentation in library_topic.PRESENTATIONS.list:
            combo_box_presentation.Append(presentation.title, presentation)

        idx = combo_box_presentation.FindString(self._plot_context.presentation.title)
        combo_box_presentation.Select(idx)

        self.combo_box_measurement_color = xrc.XRCCTRL(self.frame, "combo_box_measurement_color")
        self.combo_box_measurement_color.Append(COLORS)
        self.combo_box_measurement_color.Select(0)

        self.text_ctrl_measurement_topic = xrc.XRCCTRL(self.frame, "text_ctrl_measurement_topic")
        self.text_ctrl_measurement_topic.Value = library_topic.ResultAttributes.getdatetime()

        self.label_coordinates = xrc.XRCCTRL(self.frame, "label_coordinates")
        self.plotpanel.canvas.mpl_connect("motion_notify_event", self.UpdateStatusBar)

        # final setup ------------------
        self.frame.Show()

        self.SetTopWindow(self.frame)

        self.plotpanel.init_plot_data()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(1000)    # 1 second interval

        return True

    def OnTimer(self, event):
        # do whatever you want to do every second here

        is_measurment_running = FILELOCK_GUI.is_measurment_running()
        logger.debug(f'OnTimer() is_measurment_running={is_measurment_running}')
        self.button_start.Enabled = not is_measurment_running
        self.button_stop.Enabled = is_measurment_running

    def UpdateStatusBar(self, event):
        if event.inaxes:
            self.label_coordinates.SetLabel(f"x={event.xdata:e}  y={event.ydata:e}")

    def OnOpenDirectory(self, event):
        self._plot_context.open_directory_in_explorer()

    def OnDisplayClone(self, event):
        self._plot_context.open_display_clone()

    def OnRestart(self, event):
        pass
