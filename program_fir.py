import os
import math
import time
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
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

useful_part = 0.6 # depending on the downsampling, useful part is the non influenced part by the low pass filtering

class FIR:
  def __init__(self, out):
    self.out = out
    self.array = np.empty(0, dtype=np.float)

  def init(self, stage, dt_s):
    self.stage = stage
    self.dt_s = dt_s
    self.out.init(stage=stage+1, dt_s=dt_s*DECIMATE_FACTOR)

  def push(self, array_in):
    assert len(array_in) <= SAMPLES_INPUT
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

SAMPLES_DENSITY = 2**12

class Density:
  def __init__(self, out, directory='.', interval_s=0.9):
    self.out = out
    self.time_s = 0.0
    self.next_s = 0.0
    self.frequencies = None
    self.Pxx_sum = None
    self.Pxx_n = 0
    self.directory = directory
    self.interval_s = interval_s

  def init(self, stage, dt_s):
    self.stage = stage
    self.dt_s = dt_s
    self.out.init(stage=stage, dt_s=dt_s)

  def flush(self):
    self.out.flush()

  def push(self, array_in):
    self.time_s += self.dt_s * len(array_in)
    if self.time_s > self.next_s:
      self.next_s += self.interval_s
      # self.next_s = self.time_s + self.interval_s
      self.density(array_in)

    self.out.push(array_in)

  def density(self, array_in):
    array_density = array_in
    if len(array_in) > SAMPLES_DENSITY:
      array_density = array_in[:SAMPLES_DENSITY]

    print(f'Stage {self.stage:02d}: Density: {self.dt_s:016.12f}, len(self.array)={len(array_in)} -> {len(array_density)}')

    self.frequencies, Pxx = scipy.signal.periodogram(array_density, 1/self.dt_s, window='hamming',) #Hz, V^2/Hz
    self.__density_averaging(array_density, Pxx)

    fig, ax = plt.subplots()
    color = 'blue'
    if self.Pxx_sum is not None:
      # If we have averaged values, use it
      Pxx = self.Pxx_sum/self.Pxx_n
      if self.Pxx_n == 1:
        color = 'fuchsia'
    Dxx = np.sqrt(Pxx) # V/Hz^0.5
    ax.loglog(self.frequencies, Dxx, linewidth=0.1, color=color)
    plt.ylabel(f'Density stage dt_s {self.dt_s:.3e}s ')
    #plt.ylim( 1e-8,1e-6)

    #plt.xlim(1e2, 1e5)
    f_limit_low = 1.0/self.dt_s/2.0 * useful_part
    f_limit_high = 1.0/self.dt_s/2.0
    plt.axvspan(f_limit_low, f_limit_high, color='red', alpha=0.2)
    plt.grid(True)
    fig.savefig(f'{self.directory}/density_{self.stage:02d}_{self.dt_s:016.12f}.png')
    fig.clf()
    plt.close(fig)
    plt.clf()

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


class DensitySummary:
  def __init__(self, list_density, directory='.'):
    self.directory = directory
    self.list_density = list_density
    summary_f = program_config_frequencies.eseries(series='E12', minimal=1e-6, maximal=1e8)
    self.summary_f = np.array(summary_f)
    self.summary_d = np.zeros(len(self.summary_f), dtype=float)
    self.summary_n = np.zeros(len(self.summary_f), dtype=int)
    for density in list_density:
      assert isinstance(density, Density)
      if density.Pxx_sum is None:
        continue
      Pxx = density.Pxx_sum / density.Pxx_n
      for idx in range(len(density.frequencies)):
        f = density.frequencies[idx]
        d = Pxx[idx]
        if f == 0:
          # frequency not required in summary
          continue
        if f > 1.0/density.dt_s/2.0 * useful_part:
          # frequency not required in summary
          continue
        nearest_idx = self.__find_nearest(self.summary_f, f)
        self.summary_n[nearest_idx] += 1
        self.summary_d[nearest_idx] += d
  
    # Calculate average
    for idx in range(len(self.summary_f)):
      n = self.summary_n[idx]
      if n == 0:
        continue
      self.summary_d[idx] = math.sqrt(self.summary_d[idx] / n)

  def __find_nearest(self, frequencies, frequency):
    best_idx = 0
    best_diff = 1e24
    for idx, f in enumerate(frequencies):
      diff = abs(frequency-f)
      if diff < best_diff:
        best_diff = diff
        best_idx = idx
      if idx > best_idx:
        # Save time and bail out
        break
    return best_idx

  def plot(self):
    filename_summary = os.path.join(self.directory, 'summary.txt')
    np.savetxt(filename_summary,
      np.transpose((self.summary_f, self.summary_d)),
      fmt='%.5e', 
      delimiter='\t',
      newline='\n', 
      header='',
      footer='', 
      comments='# ',
      encoding=None
    )

    fig, ax = plt.subplots()
    # An array with True/False values. True, if the bin-count > 0.5
    mask = np.array([v > 0.5 for v in self.summary_n])
    f = self.summary_f[mask]
    d = self.summary_d[mask]
    ax.loglog(f, d, linestyle='', marker='o', markersize=2, color='blue')
    plt.ylabel(f'Density [V/Hz^0.5]')
    #plt.ylim( 1e-11,1e-6)
    plt.xlim(1e-2, 1e5) # temp Peter
    plt.grid(True)
    fig.savefig(f'{self.directory}/density.png')
    fig.clf()
    plt.close(fig)
    plt.clf()

class OutTrash:
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
  def __init__(self, fir_count=FIR_COUNT):
    import time
    import program

    self.list_density = []
    self.start = time.time()
    o = OutTrash()

    for i in range(fir_count):
      o = Density(o, directory=program.DIRECTORY_1_CONDENSED)
      self.list_density.append(o)
      o = FIR(o)

    o = Density(o, directory=program.DIRECTORY_1_CONDENSED)
    self.output = o
  
  def plot(self):
    import time
    import program
    ds = DensitySummary(self.list_density, directory=program.DIRECTORY_1_CONDENSED)
    ds.plot()

    print(f'Duration {time.time()-self.start:0.2f}')
