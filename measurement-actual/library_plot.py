import re
import time
import random
import pickle
import pathlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.animation

plt.rcParams['toolbar'] = 'toolmanager'
from matplotlib.backend_tools import ToolBase

class ListTools(ToolBase):
    '''List all the tools controlled by the `ToolManager`'''
    # keyboard shortcut
    default_keymap = 'm'
    description = 'List Tools'

    def trigger(self, *args, **kwargs):
        print('_' * 80)
        print("{0:12} {1:45} {2}".format(
            'Name (id)', 'Tool description', 'Keymap'))
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

class UserAutozoom(ToolBase):
    '''Peter Autozoom'''
    # keyboard shortcut
    default_keymap = 'z'
    description = 'Auto Zoom'
    def trigger(self, *args, **kwargs):
        for ax in self.figure.get_axes():
            ax.autoscale()
        self.figure.canvas.draw()

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
  def __init__(self, f, d):
    self.f = f
    self.d = d

    self.x_filename = None
    self.x_directory = None

  def __getstate__(self):
    # Only these elements will be pickled
    return { 'f': self.f, 'd': self.d } 

  @classmethod
  def filename(cls, directory):
    return directory.joinpath('result_summary.pickle')

  @classmethod
  def save(cls, directory, f, d):
    prs = PickleResultSummary(f, d)
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
      prs = PickleResultSummary(f=[], d=[])
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

    return changed

class Topic:
  def __init__(self, ra, prs):
    assert isinstance(ra, ResultAttributes)
    assert isinstance(prs, PickleResultSummary)
    self.__ra = ra
    self.__prs = prs
    self.__plot_line = None
  
  def set_plot_line(self, plot_line):
    self.__plot_line = plot_line

  def reload_if_changed(self):
    assert self.__plot_line is not None
    changed = self.__prs.reload_if_changed()
    if changed:
      self.__plot_line.set_data(self.__prs.f, self.__prs.d)
    return changed

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

class PlotData:
  def __init__(self, filename):
    curdir = pathlib.Path(filename).absolute().parent
    self.listTopics = []
    for dir_raw in curdir.glob(ResultAttributes.RESULT_DIR_PATTERN):
      if not dir_raw.is_dir():
        continue
      self.listTopics.append(Topic.load(dir_raw))

def do_plot(plotData, title, do_show=False, do_write_files=False, do_animate=False):
    fig, ax = plt.subplots()
    plt.title(title)
    fig.canvas.manager.toolmanager.add_tool('List', ListTools)
    fig.canvas.manager.toolmanager.add_tool('Autozoom', UserAutozoom)
    fig.canvas.manager.toolbar.add_tool('Autozoom', 'navigation', 1)

    for topic in plotData.listTopics:
      plot_line, = ax.loglog(
        topic.f,
        topic.d,
        linestyle='none',
        linewidth=0.1,
        marker='.',
        markersize=3, 
        color=topic.color,
        label=topic.topic
      )
      topic.set_plot_line(plot_line)

    plt.ylabel(f'Density [V/Hz^0.5]')
    plt.xlabel(f'Frequency [Hz]')
    # plt.ylim( 1e-11,1e-6)
    # plt.xlim(1e-2, 1e5) # temp Peter
    # plt.grid(True)
    plt.grid(True, which="major", axis="both", linestyle="-", color='gray', linewidth=0.5)
    plt.grid(True, which="minor", axis="both", linestyle="-", color='silver', linewidth=0.1)
    ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=20))
    ax.legend(loc='lower left', shadow=True, fancybox=False)

    if do_write_files:
      for ext in ('png', 'svg'):
        filename = pathlib.Path(__file__).parent.joinpath(f'result_density.{ext}')
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
                      interval=2000, # Delay between frames in milliseconds
                      init_func=None, # A function used to draw a clear frame. If not given, the results of drawing from the first item in the frames sequence will be used.
                      repeat=False) 

      plt.show()
