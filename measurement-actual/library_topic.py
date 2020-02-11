import re
import time
import types
import pickle
import pathlib
import numpy as np

DIRECTORY_NAME_RAW_PREFIX='raw-'

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
  def getdatetime(cls):
    return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())

  @classmethod
  def result_dir_actual(cls, directory_name=None):
    if directory_name is None:
      return f'{DIRECTORY_NAME_RAW_PREFIX}red-{cls.getdatetime()}'
    assert directory_name.startswith(DIRECTORY_NAME_RAW_PREFIX)
    return directory_name

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

  def get_as_dict(self):
    return dict(
      topic=self.topic,
      raw_data = dict(
        d=self.d,
        f=self.f,
        enbw=self.enbw,
      ),
      presentations = PRESENTATIONS.get_as_dict(self)
    )

  def set_plot_line(self, plot_line):
    self.__plot_line = plot_line

  def reload_if_changed(self, presentation):
    assert self.__plot_line is not None
    start = time.time()
    changed = self.__prs.reload_if_changed()
    if changed:
      self.recalculate_data(presentation)
      print(f'changed {time.time()-start:0.2f}s "{self.__ra.topic}"')
    return changed

  def recalculate_data(self, presentation):
    x, y = presentation.get_xy(self)
    self.__plot_line.set_data(x, y)

  def clear_line(self):
    if self.__plot_line is None:
      return
    self.__plot_line.remove()
    del self.__plot_line
    self.__plot_line = None

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
  
  def get_as_dict(self, topic):
    x, y = self.get_xy(topic)
    return dict(
      tag = self.tag,
      help_text = self.help_text,
      y_label = self.y_label,
      x = x,
      y = y,
    )

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

  def get_as_dict(self, topic):
    return {p.tag:p.get_as_dict(topic) for p in self.list}

PRESENTATIONS = Presentations()

import time
class PlotDataMultipleDirectories:
  def __init__(self, filename):
    self.topdir = pathlib.Path(filename).absolute().parent
    self.__load_data()

  def __load_data(self):
    list_directories = self.read_directories()
    self.set_directories = {d.name for d in list_directories}
    self.listTopics = [Topic.load(d) for d in list_directories]
    self.listTopics.sort(key=lambda topic: topic.topic.upper())

  def read_directories(self):
    list_directories = []
    for dir_raw in self.topdir.glob(ResultAttributes.RESULT_DIR_PATTERN):
      if not dir_raw.is_dir():
        continue
      list_directories.append(dir_raw)
    return list_directories

  def directories_changed(self):
    set_directories_new = {d.name for d in self.read_directories()}
    return self.set_directories != set_directories_new

  def remove_lines_and_reload_data(self, fig, ax):
    for topic in self.listTopics:
      topic.clear_line()
    ax.legend().remove()

    self.__load_data()

    fig.canvas.draw()

class PlotDataSingleDirectory:
  def __init__(self, dir_raw):
    self.listTopics = [
      Topic.load(dir_raw)
    ]
