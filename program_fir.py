import time
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt

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

# From datafile
# TODO: Read from file
FILE_adu = 3.0518509475997192e-06
FILE_dt_s = 1.6e-08

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
      self.density(array_in)

    self.out.push(array_in)

  def density(self, array_in):
    array_density = array_in
    if len(array_in) > SAMPLES_DENSITY:
      array_density = array_in[:SAMPLES_DENSITY]

    print(f'Stage {self.stage:02d}: Density: {self.dt_s:016.12f}, len(self.array)={len(array_in)} -> {len(array_density)}')

    f, Pxx = scipy.signal.periodogram(array_density, 1/self.dt_s, window='hamming',) #Hz, V^2/Hz
    self.__density_averaging(array_density, Pxx)

    fig, ax = plt.subplots()
    color = 'blue'
    if self.Pxx_sum is not None:
      # If we have averaged values, use it
      Pxx = self.Pxx_sum/self.Pxx_n
      if self.Pxx_n == 1:
        color = 'fuchsia'
    Dxx = np.sqrt(Pxx) # V/Hz^0.5
    ax.loglog(f, Dxx, linewidth=0.1, color=color)
    plt.ylabel(f'Density stage dt_s {self.dt_s:.3e}s ')
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
  def __init__(self, out, filename):
    self.out = out
    self.filename = filename
    out.init(stage=0, dt_s=FILE_dt_s)

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
        rawA = np.frombuffer(data_bytes, dtype=np.int16)
        buf_V = FILE_adu * rawA

        self.out.push(buf_V)

class InSin:
  def __init__(self, out, time_total_s=10, dt_s=0.01):
    self.out = out
    self.time_total_s = time_total_s
    self.dt_s = dt_s

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


if __name__ == '__main__':
  #
  #
  #

  start = time.time()
  o = OutTrash()

  # 5*1e9 / 2 / (2**12) = 610'351 Samples
  for i in range(FIR_COUNT):
    o = Density(o)
    o = FIR(o)

  o = Density(o)
  i = InFile(o, 'C:\\Projekte\\ETH-Compact\\versuche_picoscope\\pymeas2019_noise\\0_raw_1s\\data_noise_density.a_bin')
  # i = InSin(o, time_total_s=200.0, dt_s=0.01)
  i.process()
  print(f'Duration {time.time()-start:0.2f}')

  if False:
      #
      #
      #
      o = OutTrash('file_out.data')
      for i in range(12):
        o = FIR(o)
      with open('file_in.data', 'r') as fin:
        while array in fin:
          o.push(array)

