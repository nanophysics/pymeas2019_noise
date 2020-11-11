"""
This code is base on a sample from
  Copyright (C) 2003-2004 Andrew Straw, Jeremy O'Donoghue and others

  License: This work is licensed under the PSF. A copy should be included
  with this source code, and is also available at
  https://docs.python.org/3/license.html
"""

import pathlib

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg
from matplotlib.figure import Figure

import wx
import wx.xrc as xrc

ERR_TOL = 1e-5  # floating point slop for peak-detection


class PlotContext:
    def __init__(self, figure, do_animate, func_animate=None):
        self.figure = figure
        self.do_animate = do_animate
        self.func_animate = func_animate


class PlotPanel(wx.Panel):
    def __init__(self, parent, plot_context):
        wx.Panel.__init__(self, parent, -1)
        self.fig = plot_context.figure

        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)
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
        # if False:
        #     ax = self.fig.add_subplot(111)

        #     x = np.arange(120.0) * 2 * np.pi / 60.0
        #     y = np.arange(100.0) * 2 * np.pi / 50.0
        #     self.x, self.y = np.meshgrid(x, y)
        #     z = np.sin(self.x) + np.cos(self.y)
        #     self.im = ax.imshow(z, cmap=cm.RdBu, origin="lower")

        #     zmax = np.max(z) - ERR_TOL
        #     ymax_i, xmax_i = np.nonzero(z >= zmax)
        #     if self.im.origin == "upper":
        #         ymax_i = z.shape[0] - ymax_i
        #     self.lines = ax.plot(xmax_i, ymax_i, "ko")

        self.toolbar.update()  # Not sure why this is needed - ADS

    def GetToolBar(self):
        # You will need to override GetToolBar if you are using an
        # unmanaged toolbar in your frame
        return self.toolbar

    def OnStart(self, event):
        # self.x += np.pi / 15
        # self.y += np.pi / 20
        # z = np.sin(self.x) + np.cos(self.y)
        # self.im.set_array(z)

        # zmax = np.max(z) - ERR_TOL
        # ymax_i, xmax_i = np.nonzero(z >= zmax)
        # if self.im.origin == "upper":
        #     ymax_i = z.shape[0] - ymax_i
        # self.lines[0].set_data(xmax_i, ymax_i)

        self.canvas.draw()


COLORS = (
    "blue",
    "orange",
    "black",
    "green",
    "red",
    "cyan",
    "magenta",
)

TITLES = (
    "LSD: linear spectral density [V/Hz^0.5]",
    "PSD: power spectral density [V^2/Hz]",
    "LS: linear spectrum [V rms]",
    "PS: power spectrum [V^2]",
    "INTEGRAL: integral [V rms]",
    "DECADE: decade left of the point [V rms]",
    "STEPSIZE: count samples [samples/s]",
    "TIMESERIE: sample [V]",
)


class MyApp(wx.App):
    def __init__(self, plot_context):
        self._plot_context = plot_context
        self.res = None
        self.frame = None
        self.panel = None
        self.plotpanel = None
        wx.App.__init__(self)

    def OnInit(self):
        xrcfile = pathlib.Path(__file__).absolute().with_suffix(".xrc")
        print("loading", xrcfile)
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
        self.plotpanel = PlotPanel(plot_container, self._plot_context)
        self.plotpanel.init_plot_data()

        # wx boilerplate
        sizer.Add(self.plotpanel, 1, wx.EXPAND)
        plot_container.SetSizer(sizer)

        # start button ------------------
        button_start = xrc.XRCCTRL(self.frame, "button_measurement_start")
        button_start.Bind(wx.EVT_BUTTON, self.plotpanel.OnStart)

        # restart button ------------------
        button_restart = xrc.XRCCTRL(self.frame, "button_measurement_restart")
        button_restart.Bind(wx.EVT_BUTTON, self.OnRestart)

        # presentation combo ------------------
        combo_box_presentation = xrc.XRCCTRL(self.frame, "combo_box_presentation")
        combo_box_presentation.Bind(wx.EVT_COMBOBOX, self.OnRestart)
        for title in TITLES:
            combo_box_presentation.Append(title)
        combo_box_presentation.Select(0)

        combo_box_measurement_color = xrc.XRCCTRL(self.frame, "combo_box_measurement_color")
        combo_box_measurement_color.Bind(wx.EVT_COMBOBOX, self.OnRestart)
        for color in COLORS:
            combo_box_measurement_color.Append(color)
        combo_box_measurement_color.Select(0)

        # final setup ------------------
        self.frame.Show()

        self.SetTopWindow(self.frame)

        return True

    def OnRestart(self, event):
        bang_count = xrc.XRCCTRL(self.frame, "bang_count")
        bangs = bang_count.GetValue()
        bangs = int(bangs) + 1
        bang_count.SetValue(str(bangs))


def main():
    plot_context = PlotContext(figure=Figure((5, 4), 75), do_animate=True)
    app = MyApp(plot_context)
    app.MainLoop()


if __name__ == "__main__":
    main()
