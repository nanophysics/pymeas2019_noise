

import re
import os
import time
import logging
import numpy as np
import matplotlib.pyplot as plt

import config_measurements
import program_picoscope

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

    npzfile = np.load(self.config.get_filename_data('npz'))
    self.channelA = npzfile['A']
    self.channelD = npzfile['D']

    with open(self.config.get_filename_data('txt'), 'r') as f:
      d = eval(f.read())
    self.dt_s = d['dt_s']
    self.num_samples = d['num_samples']
    self.trigger_at = d['trigger_at']
    pass

  def write(self, channelA, channelD, dt_s, num_samples, trigger_at):
    aux_data = dict(
      dt_s = dt_s,
      num_samples = num_samples,
      trigger_at = trigger_at,
    )
    print(f'Writing')
    np.savez(self.config.get_filename_data('npz'), A=channelA, D=channelD)
    with open(self.config.get_filename_data('txt'), 'w') as f:
      f.write(str(aux_data))

  def dump_plot(self):
    # t = np.arange(-scope.pre_trigger, dt*num_samples-scope.pre_trigger, dt)
    t = np.arange(0, self.dt_s*self.num_samples, self.dt_s)
    plt.plot(t, self.channelA)

    # plt.plot(self.channelA)
    plt.ylabel('channel A')
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

  def get_filename_data(self, extension):
    filename = f'data_{self.channel_name}_{self.frequency_Hz:0.0e}hz'
    return os.path.join(DIRECTORY_RAW, f'{filename}.{extension}')

  def _update_element(self, key, value):
    assert key in self.__dict__
    self.__dict__[key] = value

  def update_by_dict(self, dict_config):
    for key, value in dict_config.items():
      self._update_element(key, value)

  def update_by_channel_file(self, filename_channel):
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

  def measure_for_all_frequencies(self):
    picoscope = program_picoscope.PicoScope()
    picoscope.connect()
    for config in self.iter_frequencies():
      # picoscope.acquire(channel_name='ch1', frequency_hz=config.frequency_Hz, duration_s=config.duration_s, amplitude_Vpp=config.input_set_Vp)
      picoscope.acquire(config)
  
  def condense(self):
    measurementData = MeasurementData(self, read=True)
    measurementData.dump_plot()
    pass

  def condense_for_all_frequencies(self):
    for config in self.iter_frequencies():
      config.condense()

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

class PyMeas2019:
  def __init__(self):
    for directory in (DIRECTORY_RAW, DIRECTORY_CONDENSED, DIRECTORY_RESULT):
      if not os.path.exists(directory):
        os.makedirs(directory)

# class ConfigFile:
#   def __init__(self, config_filename):
#     self.pymeas2019 = PyMeas2019()
#     self.config_filename = os.path.basename(config_filename)
#     self.dict_channel = {}
#     self.dict_channel.update(config_measurements.defaults)

#     with open(config_filename) as f:
#       dict_globals = {}
#       exec(f.read(), dict_globals)
#       self.dict_channel.update(dict_globals['config'])

#     match = RE_CONFIG_CHANNEL.match(self.config_filename)

#     assert match is not None
#     channel_name = match.group('channel')
#     self.dict_channel['channel_name'] = channel_name

#     pass

if __name__ == '__main__':
  print('get_configs: {}'.format(get_configs()))
  for config_filename in get_configs():
    config = get_config_by_config_filename(config_filename)
    config.condense_for_all_frequencies()
