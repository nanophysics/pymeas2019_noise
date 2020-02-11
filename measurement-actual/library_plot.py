import re
import time
import numpy as np
import types
import pickle
import pathlib
import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.animation
import matplotlib.backend_tools
import matplotlib.artist as artist
matplotlib.use('TkAgg')
# Hide messages like:
#   Treat the new Tool classes introduced in v1.5 as experimental for now, the API will likely change in version 2.1 and perhaps the rcParam as well
import warnings
warnings.filterwarnings(action='ignore')

def x():
  import tkinter
  import tkinter.ttk

  window = tkinter.Tk()

  window.title("Python Tkinter Text Box")
  window.minsize(600,400)

  def clickStart():
    label.configure(text= 'Hello ' + name.get())

  label = tkinter.ttk.Label(window, text = "Enter Your Name")
  label.grid(column = 0, row = 0)

  name = tkinter.StringVar()
  nameEntered = tkinter.ttk.Entry(window, width = 15, textvariable = name)
  nameEntered.grid(column = 0, row = 1)

  button = tkinter.ttk.Button(window, text = "Start Measurement", command = clickStart)
  button.grid(column= 0, row = 2)

  window.mainloop()

  pass

class UserSelectPresentation(matplotlib.backend_tools.ToolBase):
  # keyboard shortcut
  description = 'Select Presentation'

  def selectPresentation(self):
    import tkinter
    import tkinter.ttk
    dialog = tkinter.Tk() 
    dialog.geometry('800x100')
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(0, weight=1)
    dialog.rowconfigure(1, weight=1)

    labelTop = tkinter.Label(dialog, text='Select a presentation')
    labelTop.grid(column=0, row=0, sticky=tkinter.EW)

    labels = [f'{p.tag}: {p.y_label}' for p in PRESENTATIONS.list]
    # combobox = tkinter.Listbox(dialog, values=labels)
    combobox = tkinter.ttk.Combobox(dialog, values=labels)
    combobox.grid(column=0, row=1, sticky=tkinter.EW)
    combobox.current(0)

    class Globals: pass
    globals = Globals()
    globals.selected = None

    def callbackFunc(event):
      globals.selected = PRESENTATIONS.list[combobox.current()]
      print(f'Selected:  {globals.selected.tag}')
      dialog.quit()

    combobox.bind("<<ComboboxSelected>>", callbackFunc)

    dialog.mainloop()
    dialog.destroy()
    return globals.selected

  def trigger(self, *args, **kwargs):
    matplotlib.backend_tools.ToolBase.trigger(self, *args, **kwargs)
    presentation = self.selectPresentation()
    if presentation == None:
      return
    globals.update_presentation(presentation=presentation)

class ListTools(matplotlib.backend_tools.ToolBase):
  '''List all the tools controlled by the `ToolManager`'''
  # keyboard shortcut
  default_keymap = 'm'
  description = 'List Tools'

  def trigger(self, *args, **kwargs):
    print('_' * 80)
    print(f"{'Name (id)':12} {'Tool description':45} {'Keymap'}")
    print('-' * 80)
    tools = self.toolmanager.tools
    for name in sorted(tools):
      if not tools[name].description:
          continue
      keys = ', '.join(sorted(self.toolmanager.get_tool_keymap(name)))
      print("{0:12} {1:45} {2}".format(
          name, tools[name].description, keys))
    print('_' * 80)
    print("Active Toggle tools")
    print("{0:12} {1:45}".format("Group", "Active"))
    print('-' * 80)
    for group, active in self.toolmanager.active_toggle.items():
      print("{0:12} {1:45}".format(str(group), str(active)))

class UserAutozoom(matplotlib.backend_tools.ToolBase):
  default_keymap = 'z'
  description = 'Auto Zoom'
  def trigger(self, *args, **kwargs):
    for ax in self.figure.get_axes():
      ax.relim()
      ax.autoscale()
    self.figure.canvas.draw()
    print('Did Autozoom')

class UserMeasurementStart(matplotlib.backend_tools.ToolToggleBase):
  # keyboard shortcut
  default_keymap = 'p'
  description = 'Measurement Start/Stop'
  def trigger(self, *args, **kwargs):
    matplotlib.backend_tools.ToolToggleBase.trigger(self, *args, **kwargs)
    if self.toggled:
      print('Start')
      x()
    else:
      print('Stop')

colors=(
  'blue',
  'orange',
  'black',
  'green',
  'red',
  'cyan',
  'magenta',
  # 'yellow',
)

class ResultAttributes:
  RESULT_DIR_PATTERN='raw-*'
  REG_DIR=re.compile(r'^raw-(?P<color>.+?)-(?P<topic>.+)$')

  def __init__(self, dir_raw):
    self.dir_raw = dir_raw
    match = ResultAttributes.REG_DIR.match(dir_raw.name)
    if match is None:
      raise Exception(f'Expected directory {dir_raw.name} to match the pattern "result-color-topic"!')
    d = match.groupdict()
    self.color = d['color']
    self.topic = d['topic']

  @classmethod
  def result_dir_actual(cls):
    color = 'red' #  random.choice(colors)
    return time.strftime('raw-' + color + '-%Y-%m-%d_%H-%M-%S', time.localtime())

class PickleResultSummary:
  def __init__(self, f, d, enbw):
    self.f = f
    self.d = d
    self.enbw = enbw

    self.x_filename = None
    self.x_directory = None

  def __getstate__(self):
    # Only these elements will be pickled
    return { 'f': self.f, 'd': self.d, 'enbw': self.enbw } 

  @classmethod
  def filename(cls, directory):
    return directory.joinpath('result_summary.pickle')

  @classmethod
  def save(cls, directory, f, d, enbw):
    prs = PickleResultSummary(f, d, enbw)
    filename_summary_pickle = cls.filename(directory)
    with open(filename_summary_pickle, 'wb') as f:
      pickle.dump(prs, f)
  
  @classmethod
  def load(cls, directory):
    filename_summary_pickle = cls.filename(directory)
    prs = None
    if filename_summary_pickle.exists():
      with open(filename_summary_pickle, 'rb') as f:
        try:
          prs = pickle.load(f)
        except pickle.UnpicklingError as e:
          print(f'ERROR Unpicking f{filename_summary_pickle.name}: {e}')
      assert isinstance(prs, PickleResultSummary)
    if prs is None:
      # The summary file has not been calculated yet.
      prs = PickleResultSummary(f=[], d=[], enbw=[])
    prs.x_directory = directory
    prs.x_filename = filename_summary_pickle
    return prs

  def reload_if_changed(self):
    import run_1_condense
    changed = run_1_condense.reload_if_changed(self.x_directory)
    if changed:
      # File has changed
      prs = PickleResultSummary.load(self.x_directory)
      self.f = prs.f
      self.d = prs.d
      self.enbw = prs.enbw

    return changed

class Topic:
  def __init__(self, ra, prs):
    assert isinstance(ra, ResultAttributes)
    assert isinstance(prs, PickleResultSummary)
    self.__ra = ra
    self.__prs = prs
    self.__plot_line = None
    self.toggle = True

  def set_plot_line(self, plot_line):
    self.__plot_line = plot_line

  def reload_if_changed(self):
    assert self.__plot_line is not None
    import time
    start = time.time()
    changed = self.__prs.reload_if_changed()
    if changed:
      self.recalculate_data()
      print(f'changed {self.__ra.topic} {changed} {time.time()-start:0.2f}s')
    return changed

  def recalculate_data(self):
    x, y = globals.presentation.get_xy(self)
    self.__plot_line.set_data(x, y)

  @classmethod
  def load(cls, dir_raw):
    prs = PickleResultSummary.load(dir_raw)
    ra = ResultAttributes(dir_raw=dir_raw)
    return Topic(ra, prs)

  @property
  def topic(self):
    return self.__ra.topic  

  @property
  def color(self):
    return self.__ra.color  

  @property
  def f(self):
    return self.__prs.f  

  @property
  def d(self):
    return self.__prs.d

  @property
  def enbw(self):
    return self.__prs.enbw

  @property
  def scaling_LSD(self):
    return self.d

  @property
  def scaling_PSD(self):
    return np.square(self.d)

  @property
  def scaling_LS(self):
    return np.multiply(self.d, np.sqrt(self.enbw))

  @property
  def scaling_PS(self):
    return np.multiply(self.scaling_PSD, self.enbw)

  @property
  def scaling_INTEGRAL(self):
    return np.sqrt(np.cumsum(self.scaling_PS)) # todo: start sum above frequency_complete_low_limit

  @property
  def decade_f_d(self):
    '''
    return f, d
    '''
    return self.__xy_decade_from_INTEGRAL(self.f, self.scaling_INTEGRAL)

  def __xy_decade_from_INTEGRAL(self, f, v):
    '''
    Returns frequency and density per decade.
    '''
    f_decade = []
    value_decade = []
    last_value = None
    def is_border_decade(f):
      return abs(f * 10**-(round(np.log10(f))) - 1.0 ) < 1E-6
    for (f, value) in zip(f, v):
      if is_border_decade(f):
        if last_value is not None:
          f_decade.append(f)
          value_decade.append(np.sqrt(value**2-last_value**2))
        last_value = value
    return f_decade, value_decade

class Presentation:
  def __init__(self, tag, help_text, xy_func, y_label):
    assert isinstance(tag, str)
    assert isinstance(help_text, str)
    assert isinstance(xy_func, types.FunctionType)
    assert isinstance(y_label, str)
    self.tag = tag
    self.help_text = help_text
    self.__xy_func = xy_func
    self.y_label = y_label

  def get_xy(self, topic):
    return self.__xy_func(topic)

class Presentations:
  def __init__(self):
    self.list = (
      Presentation(
        tag = 'LSD',
        y_label = 'linear spectral density [V/Hz^0.5]',
        help_text = 'linear spectral density [V/Hz^0.5] represents the noise density. Useful to describe random noise.',
        xy_func = lambda topic: (topic.f, topic.scaling_LSD),
      ),
      Presentation(
        tag = 'PSD',
        y_label = 'power spectral density [V^2/Hz]',
        help_text = 'power spectral density [V^2/Hz] ist just the square of the LSD. This representation of random noise is useful if you want to sum up the signal over a given frequency interval. ',
        xy_func = lambda topic: (topic.f, topic.scaling_PSD)
      ),
      Presentation(
        tag = 'LS',
        y_label = 'linear spectrum [V rms]',
        help_text = 'linear spectrum [V rms] represents the voltage in a frequency range. Useful if you want to measure the amplitude of a sinusoidal signal.',
        xy_func = lambda topic: (topic.f, topic.scaling_LS)
      ),
      Presentation(
        tag = 'PS',
        y_label = 'power spectrum [V^2]',
        help_text = 'power spectrum [V^2] represents the square of LS. Useful if you want to measure the amplitude of a sinusoidal signal which is just between two frequency bins. You can now add the two values to get the amplitude of the sinusoidal signal.',
        xy_func = lambda topic: (topic.f, topic.scaling_PS),
      ),
      Presentation(
        tag = 'INTEGRAL',
        y_label = 'integral [V rms]',
        help_text = 'integral [V rms] represents the integrated voltage from the lowest measured frequency up to the actual frequency. Example: Value at 1 kHz: is the voltage between 0.01 Hz and 1 kHz.',
        xy_func = lambda topic: (topic.f, topic.scaling_INTEGRAL),
      ),
      Presentation(
        tag = 'DECADE',
        y_label = 'decade left of the point [V rms]',
        help_text = 'decade left of the point [V rms] Example: The value at 100 Hz represents the voltage between 100Hz/10 = 10 Hz and 100 Hz.',
        xy_func = lambda topic: topic.decade_f_d
      ),
    )

    self.tags = [p.tag for p in self.list]
    self.dict = {p.tag:p for p in self.list}

  def get(self, tag):
    try:
      return self.dict[tag]
    except KeyError:
      raise Exception(f'Presentation {tag} not found! Choose one of {self.tags}.')

PRESENTATIONS = Presentations()

class PlotDataMultipleDirectories:
  def __init__(self, filename):
    curdir = pathlib.Path(filename).absolute().parent
    self.listTopics = []
    for dir_raw in curdir.glob(ResultAttributes.RESULT_DIR_PATTERN):
      if not dir_raw.is_dir():
        continue
      self.listTopics.append(Topic.load(dir_raw))

    self.listTopics.sort(key=lambda topic: topic.topic.upper()) 

class PlotDataSingleDirectory:
  def __init__(self, dir_raw):
    self.listTopics = [
      Topic.load(dir_raw)
    ]

class Globals:
  def __init__(self):
    self.presentation = None
    self.plotData = None
    self.fig = None

  def set(self, plotData, fig):
    # assert self.plotData is None
    # assert self.fig is None
    self.plotData = plotData
    self.fig = fig

  def update_presentation(self, presentation=None, update=True):
    if presentation is not None:
      self.presentation = presentation
    if update:
      assert self.plotData is not None
      plt.ylabel(f'{self.presentation.tag}: {self.presentation.y_label}')
      for topic in self.plotData.listTopics:
        topic.recalculate_data()
      for ax in self.fig.get_axes():
        ax.relim()
        ax.autoscale()
      self.fig.canvas.draw()

globals = Globals()


def do_plots(**args):
  '''
  Print all presentation (LSD, LS, PS, etc.)
  '''
  for tag in PRESENTATIONS.tags:
    do_plot(presentation_tag=tag, **args)

def do_plot(plotData, title=None, do_show=False, write_files=('png', 'svg'), write_files_directory=None, do_animate=False, show_legend=True, presentation_tag='LSD'):
  globals.update_presentation(PRESENTATIONS.get(presentation_tag), update=False)

  plt.rcParams['toolbar'] = 'toolmanager'

  fig, ax = plt.subplots()
  globals.set(plotData, fig)
  if title:
    plt.title(title)
  fig.canvas.manager.toolmanager.add_tool('List', ListTools)
  fig.canvas.manager.toolmanager.add_tool('Autozoom', UserAutozoom)
  fig.canvas.manager.toolbar.add_tool('Autozoom', 'navigation', 1)

  fig.canvas.manager.toolmanager.add_tool('Start/Stop', UserMeasurementStart)
  fig.canvas.manager.toolbar.add_tool('Start/Stop', 'navigation', 1)

  fig.canvas.manager.toolmanager.add_tool('Presentation', UserSelectPresentation)
  fig.canvas.manager.toolbar.add_tool('Presentation', 'navigation', 1)

  for topic in plotData.listTopics:
    x, y = globals.presentation.get_xy(topic)
    plot_line, = ax.loglog(
      x, y,
      linestyle='none',
      linewidth=0.1,
      marker='.',
      markersize=3, 
      color=topic.color,
      label=topic.topic
    )
    topic.set_plot_line(plot_line)

  plt.xlabel('Frequency [Hz]')
  plt.grid(True, which="major", axis="both", linestyle="-", color='gray', linewidth=0.5)
  plt.grid(True, which="minor", axis="both", linestyle="-", color='silver', linewidth=0.1)
  ax.xaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10.0, numticks=20))
  if show_legend:
    ax.legend(fancybox=True, framealpha=0.5)
    leg = plt.legend()
    leg.get_frame().set_linewidth(0.0)

  globals.update_presentation()

  if write_files_directory is None:
    # The current directory
    write_files_directory = pathlib.Path(__file__).parent

  for ext in write_files:
    filename = write_files_directory.joinpath(f'result_{globals.presentation.tag}.{ext}')
    print(filename)
    fig.savefig(filename, dpi=300)

  if do_show:
    plt.show()
    fig.clf()
    plt.close(fig)
    plt.clf()
    plt.close()
    return

  if do_animate:
    def animate(i):
      for topic in plotData.listTopics:
        topic.reload_if_changed()

    def endless_iter():
      while True:
        yield 42

    ani = matplotlib.animation.FuncAnimation(fig,
                    func=animate, 
                    frames=endless_iter(),
                    interval=1000, # Delay between frames in milliseconds
                    init_func=None, # A function used to draw a clear frame. If not given, the results of drawing from the first item in the frames sequence will be used.
                    repeat=False) 

    plt.show()
    return

  fig.clf()
  plt.close(fig)
  plt.clf()
  plt.close()
