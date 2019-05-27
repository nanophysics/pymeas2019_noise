
import gc
import re
import os
import math
import time
import cmath
import logging
import numpy as np
import matplotlib.pyplot as plt

import config_measurements
import program_picoscope_5442D as program_picoscope
# import program_picoscope_2204A as program_picoscope

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

import config_measurements

DIRECTORY_TOP = os.path.dirname(os.path.abspath(__file__))

DIRECTORY_RAW = os.path.join(DIRECTORY_TOP, '0_raw')
DIRECTORY_CONDENSED = os.path.join(DIRECTORY_TOP, '1_condensed')
DIRECTORY_RESULT = os.path.join(DIRECTORY_TOP, '2_result')

RE_CONFIG_CHANNEL = re.compile('run_config_(?P<channel>.*?).py')

DEFINED_BY_MEASUREMENTS='DEFINED_BY_MEASUREMENTS'
DEFINED_BY_CHANNEL='DEFINED_BY_CHANNEL'
DEFINED_BY_FREQUENCY='DEFINED_BY_FREQUENCY'

class MeasurementData:
  def __init__(self, config, read=False):
    self.config = config
    self.fA = None
    self.fD = None

    if not read:
      return

    with open(self.config.get_filename_data('txt'), 'r') as f:
      d = eval(f.read())
    self.dt_s = d['dt_s']
    self.num_samples = d['num_samples']

    self.channelA_volts_per_adu = d['channelA_volts_per_adu']
    self.channelD_volts_per_adu = d['channelD_volts_per_adu']

  def open_files(self, mode):
    assert mode in ('rb', 'wb')
    assert self.fA is None
    assert self.fD is None
    self.fA = open(self.config.get_filename_data('a_bin'), mode)
    self.fD = open(self.config.get_filename_data('d_bin'), mode)

  def close_files(self):
    assert self.fA is not None
    self.fA.close()
    self.fA=None
    assert self.fD is not None
    self.fD.close()
    self.fD=None

  def get_samples(self, num_samples_chunk):

    def read_buf(fData, adu):
      # See: msl-equipment\msl\equipment\resources\picotech\picoscope\channel.py
      # np.empty((0, 0), dtype=np.int16)
      bytes_per_sample = 2

      data_bytes = fData.read(bytes_per_sample*num_samples_chunk)
      rawA = np.frombuffer(data_bytes, dtype=np.int16)
      buf_V = adu * rawA
      return buf_V

    bufA_V = read_buf(self.fA, self.channelA_volts_per_adu)
    bufD_V = read_buf(self.fD, self.channelD_volts_per_adu)
    return bufA_V, bufD_V

  def write(self, channelA_volts_per_adu, channelD_volts_per_adu, dt_s, num_samples):
    aux_data = dict(
      channelA_volts_per_adu = channelA_volts_per_adu,
      channelD_volts_per_adu = channelD_volts_per_adu,
      dt_s = dt_s,
      num_samples = num_samples,
    )

    with open(self.config.get_filename_data('txt'), 'w') as f:
      f.write(str(aux_data))

  def calculate_transfer(self):
    # Peter
    # todo: overload
    # https://www.numpy.org/
    # https://www.scipy.org/

    print('f={:0.1f} a={} d={}:'.format(self.config.frequency_Hz, self.GainPhase(self.channelA), self.GainPhase(self.channelD)))

    channelA = self.channelA
    channalAmal2 = 2*channelA
    self.config.frequency_Hz
    self.num_samples
    pass

  def __prepareGainPhase(self, i_start, i_end, points):
    a = self.dt_s * 2 * np.pi * self.config.frequency_Hz
    phasevector = np.linspace(a * i_start, a * i_end, num=i_end-i_start)

    # corresponds to np.hanning(points)
    ivektor = np.linspace(i_start/points, i_end/points, num=i_end-i_start)
    windowvector = 1 - np.cos(2 * np.pi * ivektor)
    self.Xvector = np.sin(phasevector) * windowvector
    self.Yvector = np.cos(phasevector) * windowvector

  def __GainPhase(self, signalvector):
    Xp = np.mean(self.Xvector * signalvector)
    Yp = np.mean(self.Yvector * signalvector)
    return complex(Xp, Yp)

  def read(self):
    complexA = complex(0.0, 0.0)
    complexD = complex(0.0, 0.0)
    vector_size = 1000000
    points = self.num_samples

    self.open_files('rb')
    i_start = 0
    while True:
      bufA_V, bufD_V = self.get_samples(vector_size)
      assert len(bufA_V) == len(bufD_V)
      if len(bufA_V) == 0:
        break
      i_end = i_start + len(bufA_V)
      self.__prepareGainPhase(i_start, i_end, points)
      complexA += self.__GainPhase(bufA_V)
      complexD += self.__GainPhase(bufD_V)
      i_start = i_end

    self.close_files()

    return complexA, complexD

  def dump_plot(self):
    # t = np.arange(-scope.pre_trigger, dt*num_samples-scope.pre_trigger, dt)
    
    # t = np.arange(0, self.dt_s*self.num_samples, self.dt_s)
    # plt.plot(t, self.channelA)
    if True:
      fig, ax = plt.subplots()

      def reduce(channel):
        x_points = 1000
        reduce_factor = len(channel)//x_points
        if reduce_factor < 1:
          reduce_factor = 1
        data = channel[::reduce_factor]
        return data

      lineA, = ax.plot(reduce(self.channelA), linewidth=0.1, color='blue')
      # lineA.set_label('Channel A')

      lineD, = ax.plot(reduce(self.channelD), linewidth=0.1, color='red')
      # lineD.set_label('Channel D')
      # lineD.set_dashes([2, 2, 10, 2])  # 2pt line, 2pt break, 10pt line, 2pt break

      ax.set_title(self.config)
      # ax.legend()

      filename_png = self.config.get_filename_data(extension='png', directory=DIRECTORY_CONDENSED)
      print(f'writing: {filename_png}')
      fig.savefig(filename_png)
      fig.clf()
      # plt.show()

    if False:
      plt.plot(self.channelD)
      plt.ylabel('channel D')
      plt.show()

class Configuration:
  def __init__(self):
    self.skalierungsfaktor = DEFINED_BY_MEASUREMENTS
    self.input_Vp = DEFINED_BY_MEASUREMENTS
    self.input_set_Vp = DEFINED_BY_MEASUREMENTS
    self.channel_name = DEFINED_BY_CHANNEL
    self.diagram_legend = DEFINED_BY_CHANNEL
    self.frequency_Hz = DEFINED_BY_FREQUENCY
    self.duration_s = DEFINED_BY_FREQUENCY

  def create_directories(self):
    for directory in (DIRECTORY_RAW, DIRECTORY_CONDENSED, DIRECTORY_RESULT):
        if not os.path.exists(directory):
          os.makedirs(directory)

  def __str__(self):
    return f'{self.diagram_legend} ({self.channel_name}, {self.frequency_Hz:012.2f}hz, {self.duration_s:0.3f}s)'
    return f'{self.diagram_legend} ({self.channel_name}, {self.frequency_Hz:0.0e}hz, {self.duration_s:0.0e}s)'

  def get_filename_data(self, extension, directory=DIRECTORY_RAW):
    filename = f'data_{self.channel_name}_{self.frequency_Hz:012.2f}hz'
    # filename = f'data_{self.channel_name}_{self.frequency_Hz:0.2e}hz'
    # filename = f'data_{self.channel_name}_{self.frequency_Hz:012.2e}hz'
    # filename = f'data_{self.channel_name}_{self.frequency_Hz:06d}hz'
    return os.path.join(directory, f'{filename}.{extension}')

  def _update_element(self, key, value):
    assert key in self.__dict__
    self.__dict__[key] = value

  def update_by_dict(self, dict_config):
    for key, value in dict_config.items():
      self._update_element(key, value)

  def update_by_channel_file(self, filename_channel):
    self.create_directories()
    dict_globals = {}
    with open(filename_channel) as f:
      exec(f.read(), dict_globals)
    dict_config = dict_globals['dict_config']
    self.update_by_dict(dict_config)

    match = RE_CONFIG_CHANNEL.match(os.path.basename(filename_channel))
    assert match is not None
    channel_name = match.group('channel')
    self._update_element('channel_name', channel_name)

  def iter_frequencies(self):
    for dict_measurement in config_measurements.list_measurements:
      self.update_by_dict(dict_measurement)
      yield self

  def measure_for_all_frequencies(self, measured_only_first=False):
    picoscope = program_picoscope.PicoScope(self)
    picoscope.connect()
    for config in self.iter_frequencies():
      # picoscope.acquire(channel_name='ch1', frequency_hz=config.frequency_Hz, duration_s=config.duration_s, amplitude_Vpp=config.input_set_Vp)
      picoscope.acquire(config)
      if measured_only_first:
        return
  
  def condense(self):
    measurementData = MeasurementData(self, read=True)
    measurementData.calculate_transfer()
    measurementData.dump_plot()
    pass

  def condense_for_all_frequencies(self):
    if False:
      for config in self.iter_frequencies():
        config.condense()

    class Measurement:
      def __init__(self, measurementData):
        self.complexA, self.complexD = measurementData.read()

    start = time.time()
    list_measurement = []
    listX = []
    for config in self.iter_frequencies():
      print(f'config.frequency_Hz: {config.frequency_Hz}')
      listX.append(config.frequency_Hz)
      measurementData = MeasurementData(self, read=True)
      list_measurement.append(Measurement(measurementData))
    print('Duration {}s'.format(time.time()-start))

    print('A')

    def get_list(f):
      return list(map(f, list_measurement))

    listY = get_list(lambda m: (m.complexA/m.complexD).real)

    if False:
      # X of channel A and D
      listAY = get_list(lambda m: m.complexA.real)
      listDY = get_list(lambda m: m.complexD.real)

      fig, ax1 = plt.subplots()

      ax1.tick_params('y', colors='blue')
      lineA, = ax1.plot(listX, listAY, linewidth=1.0, color='blue')
      lineA.set_label('Channel A')

      ax2 = ax1.twinx()

      ax2.tick_params('y', colors='red')
      lineD, = ax2.plot(listX, listDY, linewidth=1.0, color='red')
      lineD.set_label('Channel D')
      # lineD.set_dashes([2, 2, 10, 2])  # 2pt line, 2pt break, 10pt line, 2pt break

      # ax.set_title(self.config)
      fig.legend()
      plt.show()
      plt.close()

    if False:
      # Phase of channel A and D
      
      listAY = get_list(lambda m: cmath.phase(m.complexA))
      listDY = get_list(lambda m: cmath.phase(m.complexD))

      fig, ax1 = plt.subplots()

      ax1.tick_params('y', colors='blue')
      lineA, = ax1.plot(listX, listAY, linewidth=1.0, color='blue')
      lineA.set_label('Channel A')

      ax2 = ax1.twinx()

      ax2.tick_params('y', colors='red')
      lineD, = ax2.plot(listX, listDY, linewidth=1.0, color='red')
      lineD.set_label('Channel D')
      # lineD.set_dashes([2, 2, 10, 2])  # 2pt line, 2pt break, 10pt line, 2pt break

      # ax.set_title(self.config)
      fig.legend()
      plt.show()
      plt.close()

    if True:
      # Phase of channel A and D
      
      listY = get_list(lambda m: (m.complexA/m.complexD).real)
      print('B')

      fig, ax1 = plt.subplots()

      ax1.tick_params('y', colors='blue')
      lineA, = ax1.plot(listX, listY, linewidth=1.0, color='blue')
      lineA.set_label('m.complexA/m.complexD')

      fig.legend()
      # filename_png = self.config.get_filename_data(extension='png', directory=DIRECTORY_CONDENSED)
      # print(f'writing: {filename_png}')
      # fig.savefig(filename_png)
      plt.show()
      plt.close()



def get_config_by_config_filename(channel_config_filename):
  config = Configuration()
  config.update_by_dict(config_measurements.dict_config)
  config.update_by_channel_file(channel_config_filename)
  return config

def get_configs():
  list_configs = []
  for filename in os.listdir(DIRECTORY_TOP):
    match = RE_CONFIG_CHANNEL.match(os.path.basename(filename))
    if match:
      list_configs.append(os.path.join(DIRECTORY_TOP, filename))
  return list_configs

def run_condense_0_to_1():
  print('get_configs: {}'.format(get_configs()))
  for config_filename in get_configs():
    config = get_config_by_config_filename(config_filename)
    config.condense_for_all_frequencies()

class PyMeas2019:
  def __init__(self):
    for directory in (DIRECTORY_RAW, DIRECTORY_CONDENSED, DIRECTORY_RESULT):
      if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == '__main__':
  if True:
    filename_config = os.path.join(DIRECTORY_TOP, 'run_config_ch1.py')
    config = get_config_by_config_filename(filename_config)
    config.measure_for_all_frequencies(measured_only_first=False)
    config.condense_for_all_frequencies()

    import sys
    sys.exit(0)

  print('get_configs: {}'.format(get_configs()))
  for config_filename in get_configs():
    config = get_config_by_config_filename(config_filename)
    config.condense_for_all_frequencies()

