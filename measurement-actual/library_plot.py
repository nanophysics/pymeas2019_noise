import re
import time
import pickle
import pathlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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
    return time.strftime('raw-red-%Y-%m-%d_%H-%M-%S', time.localtime())

class PickleResultSummary:
  def __init__(self, f, d):
    self.f = f
    self.d = d

  @classmethod
  def save(self, directory, f, d):
    prs = PickleResultSummary(f, d)
    filename_summary_pickle = f'{directory}/result_summary.pickle'
    with open(filename_summary_pickle, 'wb') as f:
      pickle.dump(prs, f)
  
  @classmethod
  def load(self, directory):
    filename_summary_pickle = f'{directory}/result_summary.pickle'
    with open(filename_summary_pickle, 'rb') as f:
      prs = pickle.load(f)
      assert isinstance(prs, PickleResultSummary)
      return prs

class Topic:
  def __init__(self, ra, prs):
    assert isinstance(ra, ResultAttributes)
    assert isinstance(prs, PickleResultSummary)
    self.__ra = ra
    self.__prs = prs
  
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
      prs = PickleResultSummary.load(dir_raw)
      ra = ResultAttributes(dir_raw=dir_raw)
      self.listTopics.append(Topic(ra, prs))

def do_plot(plotData, title, do_show: bool):
    fig, ax = plt.subplots()
    plt.title(title)

    for topic in plotData.listTopics:
      ax.loglog(
        topic.f,
        topic.d,
        linestyle='none',
        linewidth=0.1,
        marker='.',
        markersize=3, 
        color=topic.color,
        label=topic.topic
      )

    plt.ylabel(f'Density [V/Hz^0.5]')
    plt.xlabel(f'Frequency [Hz]')
    # plt.ylim( 1e-11,1e-6)
    # plt.xlim(1e-2, 1e5) # temp Peter
    # plt.grid(True)
    plt.grid(True, which="major", axis="both", linestyle="-", color='gray', linewidth=0.5)
    plt.grid(True, which="minor", axis="both", linestyle="-", color='silver', linewidth=0.1)
    ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=20))
    ax.legend(loc='lower left', shadow=True, fancybox=False)

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
