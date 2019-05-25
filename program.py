
import gc
import re
import os
import time
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

    if not read:
      return

    with open(self.config.get_filename_data('txt'), 'r') as f:
      d = eval(f.read())
    self.dt_s = d['dt_s']
    self.num_samples = d['num_samples']
    self.trigger_at = d['trigger_at']

    filenameNpz = self.config.get_filename_data('npz')
    npzfile = np.load(filenameNpz)
  
    def get_channel(s, adu):
      channel = npzfile[s]
      channel = np.roll(channel, -self.trigger_at)
      return adu * channel

    self.channelA = get_channel('A', d['channelA_volts_per_adu'])
    self.channelD = get_channel('D', d['channelD_volts_per_adu'])

  def write(self, channelA, channelD, channelA_volts_per_adu, channelD_volts_per_adu, dt_s, num_samples, trigger_at):
    aux_data = dict(
      channelA_volts_per_adu = channelA_volts_per_adu,
      channelD_volts_per_adu = channelD_volts_per_adu,
      dt_s = dt_s,
      num_samples = num_samples,
      trigger_at = trigger_at,
    )
    print(f'Writing')
    np.savez(self.config.get_filename_data('npz'), A=channelA, D=channelD)
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

  def GainPhase(self, signalvector = [1,2,3]):
    points = len(signalvector)
    timevector = np.linspace(0, points*self.dt_s, num=points)
    phasevector = timevector * 2 * np.pi * self.config.frequency_Hz
    windowvector = np.hanning(points)
    Xvector = np.sin(phasevector) * windowvector
    Yvector = np.cos(phasevector) * windowvector

    gc.collect()

    calibratesine =  np.sin(phasevector) # amplitude of 1 peak or 1/sqrt(2) rms
    Xcalibratesine = np.mean(Xvector * calibratesine)
    factor = 1 / Xcalibratesine

    Xp = np.mean(Xvector * signalvector) * factor
    Yp = np.mean(Yvector * signalvector) * factor
    return complex (Xp, Yp)

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
    self.with_channel_D = DEFINED_BY_MEASUREMENTS

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

    listAX = []
    listAY = []
    listDX = []
    listDY = []
    for config in self.iter_frequencies():
      measurementData = MeasurementData(self, read=True)

      complexA = measurementData.GainPhase(measurementData.channelA)
      listAX.append(config.frequency_Hz)
      listAY.append(complexA.real)
      # listAY.append(abs(complexA))

      complexD = measurementData.GainPhase(measurementData.channelD)
      listDX.append(config.frequency_Hz)
      listDY.append(complexD.real)
      # listDY.append(abs(complexD))

    if False:
      plt.plot(listAX, listAY)
      plt.ylabel('channel XYZ')
      plt.show()
    
    if True:
      fig, ax1 = plt.subplots()

      ax1.tick_params('y', colors='blue')
      lineA, = ax1.plot(listAX, listAY, linewidth=1.0, color='blue')
      lineA.set_label('Channel A')

      ax2 = ax1.twinx()

      ax2.tick_params('y', colors='red')
      lineD, = ax2.plot(listDX, listDY, linewidth=1.0, color='red')
      lineD.set_label('Channel D')
      # lineD.set_dashes([2, 2, 10, 2])  # 2pt line, 2pt break, 10pt line, 2pt break

      # ax.set_title(self.config)
      fig.legend()
      plt.show()



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

