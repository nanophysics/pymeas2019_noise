import os
import math
import time
import scipy.signal
import numpy as np
import pickle
import pathlib
import itertools
import threading
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import library_plot
import program
import program_config_frequencies

#   <---------------- INPUT ---------========------->
#
#  |<-- LEFT -->|<--====- SELECT -====-->|<- RIGHT ->|
#                   |<- DECIMATE ->|
DECIMATE_FACTOR = 2
SAMPLES_LEFT = 100  # 36
SAMPLES_RIGHT = 100  # 36
SAMPLES_SELECT = 910000  # 5000000
SAMPLES_INPUT = SAMPLES_LEFT + SAMPLES_SELECT + SAMPLES_RIGHT

assert SAMPLES_LEFT % DECIMATE_FACTOR == 0
assert SAMPLES_RIGHT % DECIMATE_FACTOR == 0
assert SAMPLES_SELECT % DECIMATE_FACTOR == 0

#FIR_COUNT = 18

FILENAME_TAG_SKIP = '_SKIP'

class FIR:
  '''
  Stream-Sink: Implements a Stream-Interface
  Stream-Source: Drives a output of Stream-Interface
  '''

  def __init__(self, out):
    self.out = out
    self.array = np.empty(0, dtype=np.float)

  def init(self, stage, dt_s):
    self.stage = stage
    self.dt_s = dt_s
    self.out.init(stage=stage+1, dt_s=dt_s*DECIMATE_FACTOR)

  def push(self, array_in):
    if array_in is None:
      # array_in is None: We may decimate
      if len(self.array) < SAMPLES_INPUT:
        # We do not need to decimate.
        # Give the next stage a chance to decimate!
        self.out.push(None)
        return

      # Decimate a part of the array
      array_decimate = self.decimate(self.array[:SAMPLES_INPUT])
      self.out.push(array_decimate)
      # Save the remainting part to 'self.array'
      self.array = self.array[SAMPLES_SELECT:]
      return 

    # assert len(array_in) <= SAMPLES_INPUT
    # Not enough data. Add it to 'self.array'
    self.array = np.append(self.array, array_in)


  def flush(self):
    length = len(self.array)
    if length > SAMPLES_LEFT + SAMPLES_RIGHT:
      if length % DECIMATE_FACTOR:
        # if length is odd, subtract 1 to make it even
        length -= 1
      array_decimate = self.decimate(self.array[:length])
      self.out.push(array_decimate)
    self.out.flush()

  def decimate(self, array_decimate):
    # print(f'{self.stage},', end='')
    assert len(array_decimate) > SAMPLES_LEFT + SAMPLES_RIGHT
    assert len(array_decimate) % DECIMATE_FACTOR == 0

    array_decimated = scipy.signal.decimate(
        array_decimate, DECIMATE_FACTOR, ftype='iir', zero_phase=True
    )

    assert len(array_decimated) == len(array_decimate)//DECIMATE_FACTOR
    index_from = SAMPLES_LEFT//DECIMATE_FACTOR
    index_to = len(array_decimated) + SAMPLES_RIGHT//DECIMATE_FACTOR
    array_decimated = array_decimated[index_from:index_to]
    return array_decimated

class SampleProcessConfig:
  def __init__(self, configStep, interval_s=0.9):
    self.fir_count = configStep.fir_count
    self.fir_count_skipped = configStep.fir_count_skipped
    self.stepname = configStep.stepname
    self.interval_s = interval_s


SAMPLES_DENSITY = 2**12


class Density:
  '''
  Stream-Sink: Implements a Stream-Interface
  Stream-Source: Drives a output of Stream-Interface

  This class processes the data-stream and every `self.config.interval_s` does some density calculation...
  The class DensitySummary will the access self.Pxx_sum/self.Pxx_n to create a density plot.
  '''
  def __init__(self, out, config, directory):
    # TODO: Make all members private!

    self.out = out
    self.time_s = 0.0
    self.next_s = 0.0
    self.Pxx_sum = None
    self.Pxx_n = 0
    self.config = config
    self.directory = directory
    self.__density_calculation_count = 0

  def init(self, stage, dt_s):
    self.stage = stage
    self.dt_s = dt_s
    self.out.init(stage=stage, dt_s=dt_s)

  def flush(self):
    self.out.flush()
    print(f'Density Stage {self.stage:02d} dt_s {self.dt_s:016.12f}: Density calculation count {self.__density_calculation_count}')

  def push(self, array_in):
    if array_in is None:
      self.out.push(None)
      return

    self.time_s += self.dt_s * len(array_in)
    if self.time_s > self.next_s:
      self.next_s += self.config.interval_s
      # self.next_s = self.time_s + self.interval_s
      self.density(array_in)

    self.out.push(array_in)

  def density(self, array_in):
    self.__density_calculation_count += 1

    array_density = array_in
    if len(array_in) > SAMPLES_DENSITY:
      array_density = array_in[:SAMPLES_DENSITY]

    # print('')
    # print(f'Stage {self.stage:02d} dt_s {self.dt_s:016.12f}, len(array)={len(array_in)} -> {len(array_density)}, mean V:{np.mean(array_density):0.6f}', end='')
    #print("Average: %0.9f V" % np.mean(array_density))

    self.frequencies, Pxx = scipy.signal.periodogram(
        array_density, 1/self.dt_s, window='hamming',)  # Hz, V^2/Hz
    self.__density_averaging(array_density, Pxx)

    filenameFull = DensityPlot.save(
        self.config, self.directory, self.stage, self.dt_s, self.frequencies, self.Pxx_n, self.Pxx_sum)
    if False:
      densityPeriodogram = DensityPlot(filenameFull)
      densityPeriodogram.plot(program.DIRECTORY_1_CONDENSED)

  def __density_averaging(self, array_density, Pxx):
      if len(array_density) < SAMPLES_DENSITY:
        return

      # Averaging
      self.Pxx_n += 1
      if self.Pxx_sum is None:
        self.Pxx_sum = Pxx
        return
      assert len(self.Pxx_sum) == len(Pxx)
      self.Pxx_sum += Pxx


class DensityPlot:
  @classmethod
  def save(cls, config, directory, stage, dt_s, frequencies, Pxx_n, Pxx_sum):
    skip = stage < config.fir_count_skipped
    skiptext = FILENAME_TAG_SKIP if skip else ''
    filename = f'densitystep_{config.stepname}_{stage:02d}{skiptext}.pickle'
    data = {
      'stepname': config.stepname,
      'stage': stage,
      'dt_s': dt_s,
      'frequencies': frequencies,
      'Pxx_n': Pxx_n,
      'Pxx_sum': Pxx_sum,
      'skip': skip,
    }
    filenameFull = os.path.join(directory, filename)
    with open(filenameFull, 'wb') as f:
      pickle.dump(data, f)

    return filenameFull

  @classmethod
  def plots_from_directory(cls, dir_input, skip):
    '''
      Return all plot (.pickle-files) from directory.
    '''
    for filename in os.listdir(dir_input):
      if filename.startswith('densitystep_') and filename.endswith('.pickle'):
        if skip and (FILENAME_TAG_SKIP in filename):
          continue
        filenameFull = os.path.join(dir_input, filename)
        yield DensityPlot(filenameFull)

  @classmethod
  def directory_plot(cls, directory_in, dir_plot):
    '''
      Loop for all densitystage-files in directory and plot.
    '''
    for densityPeriodogram in cls.plots_from_directory(directory_in, skip=False):
        densityPeriodogram.plot(dir_plot)

  @classmethod
  def directory_plot_thread(cls, dir_input, dir_plot):
    class WorkerThread(threading.Thread):
      def __init__(self, *args, **keywords): 
        threading.Thread.__init__(self, *args, **keywords) 
        self.__stop = False
        self.start()

      def run(self):
        while True:
          time.sleep(2.0)
          cls.directory_plot(dir_input, dir_plot)
          if self.__stop:
            return

      def stop(self):
        self.__stop = True
        self.join()

    return WorkerThread()

  def __init__(self, filenameFull):
    with open(filenameFull, 'rb') as f:
      data = pickle.load(f)
    self.stepname = data['stepname']
    self.stage = data['stage']
    self.dt_s = data['dt_s']
    self.skip = data['skip']
    self.frequencies = data['frequencies']
    self.__Pxx_n = data['Pxx_n']
    self.__Pxx_sum = data['Pxx_sum']
    print(f'DensityPlot {self.stage} {self.dt_s} {filenameFull}')

  @property
  def Pxx_n(self):
    return self.__Pxx_n

  @property
  def Pxx(self):
    if self.__Pxx_n == 0:
      return None
    return self.__Pxx_sum/self.__Pxx_n

  @property
  def Dxx(self):
    if self.__Pxx_n == 0:
      return None
    return np.sqrt(self.Pxx)  # V/Hz^0.5

  def plot(self, directory):
    if not os.path.exists(directory):
      os.mkdir(directory)
    filenameFull = f'{directory}/densitystep_{self.stepname}_{self.stage:02d}_{self.dt_s:016.12f}.png'
    if self.Pxx_n is None:
      print(f'No Pxx: skipped {filenameFull}')
      return

    # If we have averaged values, use it
    fig, ax = plt.subplots()
    color = 'fuchsia' if self.Pxx_n == 1 else 'blue'
    ax.loglog(self.frequencies, self.Dxx , linewidth=0.1, color=color)
    plt.ylabel(f'Density stage dt_s {self.dt_s:.3e}s ')
    # plt.ylim( 1e-8,1e-6)

    # plt.xlim(1e2, 1e5)
    f_limit_low = 1.0/self.dt_s/2.0 * useful_part
    f_limit_high = 1.0/self.dt_s/2.0
    plt.axvspan(f_limit_low, f_limit_high, color='red', alpha=0.2)
    plt.grid(True)
    fig.savefig(filenameFull)
    fig.clf()
    plt.close(fig)
    plt.clf()
    plt.close()

class DensityPoint:
  DELIMITER = '\t'
  def __init__(self, f, d, densityPlot):
    self.f = f
    self.d = d
    self.densityPlot = densityPlot

  @property
  def stage(self):
    return self.densityPlot.stage

  @property
  def step(self):
    return self.densityPlot.step

  @property
  def stepname(self):
    return self.densityPlot.stepname

  @property
  def skip(self):
    return self.densityPlot.skip

  @property
  def line(self):
    l = (self.stepname, str(self.stage), bool(self.skip), self.f, self.d)
    l = [str(e) for e in l]
    return DensityPoint.DELIMITER.join(l)

  # @classmethod
  # def factory(cls, line):
  #   class DensityPointRead:
  #     def __init__(self, line):
  #       l = line.split(cls.DELIMITER)
  #       self.stepname = l[0]
  #       self.stage = int(l[1])
  #       self.skip = bool(l[2])
  #       self.f = float(l[3])
  #       self.d = float(l[4])

  #   return DensityPointRead(line)

class Average:
  def __init__(self):
    self.reset()

  def reset(self):
    self.__sum_d = 0.0
    self.__sum_n = 0

  def avg(self):
    '''
    return None if no samples
    '''
    if self.__sum_n == 0:
      return None
    avg = self.__sum_d / self.__sum_n
    self.reset()
    return avg

  def sum(self, d):
    self.__sum_n += 1
    self.__sum_d += d
    
class Selector:
  def __init__(self, series='E12'):
    self.__eseries_borders = program_config_frequencies.eseries(series=series, minimal=1e-6, maximal=1e8, borders=True)

  def fill_bins(self, density, firstDensityPoint, lastDensity, trace=False):
    # contribute, fill_bins
    assert isinstance(density, DensityPlot)
    avg = Average()
    idx_fft = 0
    Pxx = density.Pxx
    list_density_points = []

    fmax_Hz = 1.0 / (density.dt_s * 2.0) # highest frequency in spectogram
    useful_part = 0.75 # depending on the downsampling, useful part is the non influenced part by the low pass filtering of the FIR stage
    f_high_limit_Hz = useful_part * fmax_Hz
    f_low_limit_Hz = f_high_limit_Hz / DECIMATE_FACTOR   # every FIR stage reduces sampling frequency by factor DECIMATE_FACTOR

    for f_eserie_left, f_eserie, f_eserie_right in self.__eseries_borders:
      if not trace:
        if f_eserie < f_low_limit_Hz:
          if not firstDensityPoint:
            continue
          # Special case for the first point: select low frequencies too

        if f_eserie > f_high_limit_Hz:
          if not lastDensity:
            # We are finished with this loop
            return list_density_points
          # Special case for the last point: select high frequencies too

      while True:
        if idx_fft >= len(density.frequencies):
          # We are finished with this loop
          return list_density_points

        f_fft = density.frequencies[idx_fft]

        if f_fft < f_eserie_left:
          idx_fft += 1
          continue

        if f_fft > f_eserie_right:
          P = avg.avg()
          if P is not None:
            d = math.sqrt(P)
            dp = DensityPoint(f=f_eserie, d=d, densityPlot=density)
            list_density_points.append(dp)
          break # Continue in next eserie.

        d = Pxx[idx_fft]
        avg.sum(d)
        idx_fft += 1

    raise Exception('Internal Programming Error')

class ColorRotator:
  # https://stackoverflow.com/questions/22408237/named-colors-in-matplotlibpy
  COLORS = 'bgrcmykw' # Attention: White at the end!
  COLORS = 'bgrcmyk'
  COLORS = (
    'blue',
    'orange',
    'black',
    'green',
    'red',
    'cyan',
    'magenta',
    # 'yellow',
  )

  def __init__(self):
    self.iter = itertools.cycle(ColorRotator.COLORS)

  @property
  def color(self):
    return next(self.iter)

class DensitySummary:
  def __init__(self, list_density, directory, trace=False):
    self.directory = directory
    self.trace = trace
    self.list_density_points = []

    list_density = self.__sort(list_density)
    for density in list_density:
      assert isinstance(density, DensityPlot)
      Pxx = density.Pxx 
      if Pxx is None:
        continue

      selector = Selector('E12')
      firstDensityPoint = len(self.list_density_points) == 0
      lastDensity = density == list_density[-1]
      list_density_points = selector.fill_bins(density, firstDensityPoint=firstDensityPoint, lastDensity=lastDensity, trace=self.trace)
      self.list_density_points.extend(list_density_points)

  def __sort(self, list_density):
    def sort_key(density):
      return density.stepname, density.dt_s

    list_density_ordered = sorted(list_density, key=sort_key, reverse=True)
    if False:
      for density in list_density_ordered:
        print(f'  {density.stepname} / {density.dt_s}')

    return list_density_ordered

  def write_summary_file(self, trace):
    file_tag = '_trace' if trace else ''
    filename_summary = f'{self.directory}/result_summary{file_tag}.txt'
    with open(filename_summary, 'w') as f:
      for dp in self.list_density_points:
        f.write(dp.line)
        f.write('\n')

  def write_summary_pickle(self):
    f = [dp.f for dp in self.list_density_points if not dp.skip]
    d = [dp.d for dp in self.list_density_points if not dp.skip]
    library_plot.PickleResultSummary.save(self.directory, f, d)

  def plot(self, file_tag='', color_given=None):
    fig, ax = plt.subplots()

    # https://matplotlib.org/3.1.1/api/markers_api.html
    MARKERS = '.+x*'
    colorRotator = ColorRotator()

    stepnames = [(stepname, list(g)) for stepname, g in itertools.groupby(self.list_density_points, lambda density: density.stepname)]
    for stepnumber, (_stepname, list_step_density) in enumerate(stepnames):

      stages = [(stage, list(g)) for stage, g in itertools.groupby(list_step_density, lambda dp: dp.stage)]
      for _stage, list_density_points in stages:
        f = [dp.f for dp in list_density_points]
        d = [dp.d for dp in list_density_points]
        color = color_fancy = colorRotator.color
        if color_given is not None:
          color = color_given
        linestyle = 'none'
        marker = '.'
        markersize = 3
        if self.trace:
          linestyle = '-'
          color = color_fancy
          dp = list_density_points[0]
          marker = MARKERS[stepnumber % len(MARKERS)]
          markersize = 2 if dp.skip else 4
        ax.loglog(f, d, linestyle=linestyle, linewidth=0.1, marker=marker, markersize=markersize, color=color)

    plt.ylabel(f'Density [V/Hz^0.5]')
    plt.xlabel(f'Frequency [Hz]')
    # plt.ylim( 1e-11,1e-6)
    # plt.xlim(1e-2, 1e5) # temp Peter
    # plt.grid(True)
    plt.grid(True, which="major", axis="both", linestyle="-", color='gray', linewidth=0.5)
    plt.grid(True, which="minor", axis="both", linestyle="-", color='silver', linewidth=0.1)
    ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=20))
    print(f'DensitySummary{file_tag}')
    filebase = f'{self.directory}/result_densitysummary{file_tag}'
    fig.savefig(filebase+'.png', dpi=300)
    # fig.savefig(filebase+'.svg')
    # plt.show()
    fig.clf()
    plt.close(fig)
    plt.clf()
    plt.close()

class OutTrash:
  '''
    Stream-Sink: Implements a Stream-Interface
  '''
  def __init__(self):
    self.array = np.empty(0, dtype=np.float)

  def init(self, stage, dt_s):
    self.stage = stage
    self.dt_s = dt_s

  def push(self, array_in):
    # self.array = np.append(self.array, array_in)

    # print(f'array={len(array)}')
    # print('OutTrash.push()')
    pass

  def flush(self):
    pass

class InFile:
  '''
  Stream-Source: Drives a output of Stream-Interface
  '''
  def __init__(self, out, filename, dt_s, volts_per_adu, skalierungsfaktor):
    self.out = out
    self.filename = filename
    self.volts_per_adu = volts_per_adu
    self.skalierungsfaktor = skalierungsfaktor
    out.init(stage=0, dt_s=dt_s)

  def process(self):
    with open(self.filename, 'rb') as fA:
      while True:
        # See: msl-equipment\msl\equipment\resources\picotech\picoscope\channel.py
        # np.empty((0, 0), dtype=np.int16)
        bytes_per_sample = 2

        num_samples_chunk = SAMPLES_INPUT

        data_bytes = fA.read(bytes_per_sample*num_samples_chunk)
        if len(data_bytes) == 0:
          self.out.flush()
          print('DONE')
          return
        raw16Bit = np.frombuffer(data_bytes, dtype=np.int16)
        buf_V = self.volts_per_adu * self.skalierungsfaktor * raw16Bit

        self.out.push(buf_V)

class InSin:
  '''
  Stream-Source: Drives a output of Stream-Interface
  '''
  def __init__(self, out, time_total_s=10.0, dt_s=0.01):
    self.out = out
    self.time_total_s = time_total_s
    self.dt_s = dt_s
    out.init(stage=0, dt_s=dt_s)

  def process(self):
    t = np.arange(0, self.time_total_s, self.dt_s)
    # nse = np.random.randn(len(t))
    r = np.exp(-t / 0.05)
    # cnse = np.convolve(nse, r) * dt_s
    # cnse = cnse[:len(t)]
    s = 1.0 * np.sin(2 * np.pi * t / 2.0) #+ 0 * cnse

    if False:
      ax.plot(s, linewidth=0.1, color='blue')

    offset = 0
    while True:
      if offset > len(s):
        self.out.flush()
        print('DONE')
        return
      self.out.push(s[offset:offset+SAMPLES_SELECT])
      offset += SAMPLES_SELECT

class SampleProcess:
  def __init__(self, config, directory_raw):
    self.config = config
    self.directory_raw = directory_raw
    o = OutTrash()

    for i in range(config.fir_count-1):
      o = Density(o, config=config, directory=self.directory_raw)
      o = FIR(o)

    o = Density(o, config=config, directory=self.directory_raw)
    self.output = o
