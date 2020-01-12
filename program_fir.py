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
import program
import program_config_frequencies

#   <---------------- INPUT ---------========------->
#
#  |<-- LEFT -->|<--====- SELECT -====-->|<- RIGHT ->|
#                   |<- DECIMATE ->|
DECIMATE_FACTOR = 2
SAMPLES_LEFT = 100 # 36
SAMPLES_RIGHT = 100 # 36
SAMPLES_SELECT = 5000000 # 284
SAMPLES_INPUT = SAMPLES_LEFT + SAMPLES_SELECT + SAMPLES_RIGHT

assert SAMPLES_LEFT % DECIMATE_FACTOR == 0
assert SAMPLES_RIGHT % DECIMATE_FACTOR == 0
assert SAMPLES_SELECT % DECIMATE_FACTOR == 0

FIR_COUNT = 18

useful_part = 0.75 # depending on the downsampling, useful part is the non influenced part by the low pass filtering

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
    # assert len(array_in) <= SAMPLES_INPUT
    samples_missing = SAMPLES_INPUT-len(self.array)
    if samples_missing > len(array_in):
      # Not enough data. Add it to 'self.array'
      self.array = np.append(self.array, array_in)
      return
    # Will up 'self.array' and push
    self.array = np.append(self.array, array_in[:samples_missing])
    array_decimate = self.decimate()
    self.out.push(array_decimate)

    # Save the remainting part to 'self.array'
    self.array = np.concatenate((self.array[SAMPLES_SELECT:], array_in[samples_missing:]))

  def flush(self):
    if len(self.array) > SAMPLES_LEFT + SAMPLES_RIGHT:
      mod_decimate = len(self.array) % DECIMATE_FACTOR
      if mod_decimate != 0:
        # Limit the last array size to fit DECIMATE_FACTOR
        self.array = self.array[0:len(self.array)-mod_decimate]
        assert len(self.array) % DECIMATE_FACTOR == 0
      array_decimate = self.decimate()
      self.out.push(array_decimate)
    self.out.flush()

  def decimate(self):
    assert len(self.array) > SAMPLES_LEFT + SAMPLES_RIGHT
    assert len(self.array) % DECIMATE_FACTOR == 0

    array_decimated = scipy.signal.decimate(self.array, DECIMATE_FACTOR, ftype='iir', zero_phase=True)

    assert len(array_decimated) == len(self.array)//DECIMATE_FACTOR
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

  def init(self, stage, dt_s):
    self.stage = stage
    self.dt_s = dt_s
    self.out.init(stage=stage, dt_s=dt_s)

  def flush(self):
    self.out.flush()

  def push(self, array_in):
    self.time_s += self.dt_s * len(array_in)
    if self.time_s > self.next_s:
      self.next_s += self.config.interval_s
      # self.next_s = self.time_s + self.interval_s
      self.density(array_in)

    self.out.push(array_in)

  def density(self, array_in):
    array_density = array_in
    if len(array_in) > SAMPLES_DENSITY:
      array_density = array_in[:SAMPLES_DENSITY]

    print(f'Stage {self.stage:02d}: Density: {self.dt_s:016.12f}, len(self.array)={len(array_in)} -> {len(array_density)}')
    print("Average: %0.9f V" % np.mean(array_density))

    self.frequencies, Pxx = scipy.signal.periodogram(array_density, 1/self.dt_s, window='hamming',) #Hz, V^2/Hz
    self.__density_averaging(array_density, Pxx)

    filenameFull = DensityPlot.save(self.config, self.directory, self.stage, self.dt_s, self.frequencies, self.Pxx_n, self.Pxx_sum)
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
    skiptext = '_SKIP' if skip else ''
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
  def plots_from_directory(cls, directory_in):
    '''
      Return all plot (.pickle-files) from directory.
    '''
    for filename in os.listdir(directory_in):
      if filename.startswith('densitystep_') and filename.endswith('.pickle'):
        filenameFull = os.path.join(directory_in, filename)
        yield DensityPlot(filenameFull)

  @classmethod
  def directory_plot(cls, directory_in, directory_out):
    '''
      Loop for all densitystage-files in directory and plot.
    '''
    for densityPeriodogram in cls.plots_from_directory(directory_in):
        densityPeriodogram.plot(directory_out)

  @classmethod
  def directory_plot_thread(cls, directory_in, directory_out):
    class WorkerThread(threading.Thread):
      def __init__(self, *args, **keywords): 
        threading.Thread.__init__(self, *args, **keywords) 
        self.__stop = False
        self.start()

      def run(self):
        while True:
          time.sleep(2.0)
          cls.directory_plot(directory_in, directory_out)
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
    ax.loglog(self.frequencies, self.Dxx, linewidth=0.1, color=color)
    plt.ylabel(f'Density stage dt_s {self.dt_s:.3e}s ')
    #plt.ylim( 1e-8,1e-6)

    #plt.xlim(1e2, 1e5)
    f_limit_low = 1.0/self.dt_s/2.0 * useful_part
    f_limit_high = 1.0/self.dt_s/2.0
    plt.axvspan(f_limit_low, f_limit_high, color='red', alpha=0.2)
    plt.grid(True)
    fig.savefig(filenameFull)
    fig.clf()
    plt.close(fig)
    plt.clf()

class DensityPoint:
  def __init__(self, f, d, densityPlot):
    self.f = f
    self.d = d
    self.densityPlot = densityPlot

  @property
  def skip(self):
    return self.densityPlot.skip

  def line(self):
    return f'{self.f} {self.d} {self.densityPlot.stepname} {self.densityPlot.stage} {self.skip}'

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
  def __init__(self, series='E12', first=False, last=True):
    self.__eseries_borders = program_config_frequencies.eseries(series=series, minimal=1e-6, maximal=1e8, borders=True)

  def fill_bins(self, density):
    # contribute, fill_bins
    assert isinstance(density, DensityPlot)
    avg = Average()
    idx_fft = 0
    Pxx = density.Pxx
    list_density_points = []

    for f_eserie_left, f_eserie, f_eserie_right in self.__eseries_borders:
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

class DensitySummary:
  def __init__(self, list_density, file_tag, directory):
    self.file_tag = file_tag
    self.directory = directory
    self.list_density_points = []

    for density in self.__sort(list_density):
      assert isinstance(density, DensityPlot)
      Pxx = density.Pxx
      if Pxx is None:
        continue

      selector = Selector('E12', first=False, last=True)
      list_density_points = selector.fill_bins(density)
      self.list_density_points.extend(list_density_points)

  def __sort(self, list_density):
    def sort_key(density):
      return density.stepname, density.dt_s

    list_density_ordered = sorted(list_density, key=sort_key)
    if True:
      for density in list_density_ordered:
        print(f'  {density.stepname} / {density.dt_s}')

    return list_density_ordered

  def plot(self):
    filename_summary = f'{self.directory}/summary_{self.file_tag}.txt'
    with open(filename_summary, 'w') as f:
      for dp in self.list_density_points:
        f.write(dp.line())
        f.write('\n')

    fig, ax = plt.subplots()

    # https://stackoverflow.com/questions/22408237/named-colors-in-matplotlibpy
    COLORS = 'bgrcmykw'
    # https://matplotlib.org/3.1.1/api/markers_api.html
    MARKERS = '.+x*'

    stepnames = [(stepname, list(g)) for stepname, g in itertools.groupby(self.list_density_points, lambda density: density.densityPlot.stepname)]
    for stepnumber, (stepname, list_step_density) in enumerate(stepnames):
      marker = MARKERS[stepnumber % len(MARKERS)]

      stages = [(stage, list(g)) for stage, g in itertools.groupby(list_step_density, lambda dp: dp.densityPlot.stage)]
      for _stage, list_density_points in stages:
        color = COLORS[_stage % len(COLORS)]
        f = [dp.f for dp in list_density_points]
        d = [dp.d for dp in list_density_points]
        linestyle = 'none'
        linestyle = '-'
        # markersize = [4 if dp.skip else 12 for dp in list_density_points]
        # markersize = 4 if dp.skip else 12
        # if dp.skip:
        #   print('skip')
        # else:
        #   print('muh')
        dp = list_density_points[0]
        markersize = 4 if dp.skip else 12
        ax.loglog(f, d, linestyle=linestyle, linewidth=0.1, marker=marker, markersize=markersize, color=color)

        # list_density_points_not_skip = [dp for dp in list_density_points if not dp.skip]
        # f = [dp.f for dp in list_density_points_not_skip]
        # d = [dp.d for dp in list_density_points_not_skip]
        # ax.loglog(f, d, linestyle=linestyle, linewidth=0.1, marker=marker, markersize=12, color=color)


    plt.ylabel(f'Density [V/Hz^0.5]')
    # plt.ylim( 1e-11,1e-6)
    # plt.xlim(1e-2, 1e5) # temp Peter
    plt.grid(True)
    print(f'DensitySummary{self.file_tag}')
    fig.savefig(f'{self.directory}/densitysummary{self.file_tag}.png')
    fig.savefig(f'{self.directory}/densitysummary{self.file_tag}.svg')
    plt.show()
    fig.clf()
    plt.close(fig)
    plt.clf()

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
    print('.', end='')

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
    #nse = np.random.randn(len(t))
    r = np.exp(-t / 0.05)
    #cnse = np.convolve(nse, r) * dt_s
    #cnse = cnse[:len(t)]
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
  def __init__(self, config, directory_raw, directory_condensed):
    self.config = config
    self.directory_raw = directory_raw
    self.directory_condensed = directory_condensed
    o = OutTrash()

    for i in range(config.fir_count):
      o = Density(o, config=config, directory=self.directory_raw)
      o = FIR(o)

    o = Density(o, config=config, directory=self.directory_raw)
    self.output = o
