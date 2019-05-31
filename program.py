
import gc
import re
import os
import math
import time
import cmath
import pprint
import logging
import numpy as np
import matplotlib.pyplot as plt

import program_config_frequencies
import program_picoscope_5442D as program_picoscope
# import program_picoscope_2204A as program_picoscope

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

DIRECTORY_TOP = os.path.dirname(os.path.abspath(__file__))

DIRECTORY_0_RAW = os.path.join(DIRECTORY_TOP, '0_raw')
DIRECTORY_1_CONDENSED = os.path.join(DIRECTORY_TOP, '1_condensed')
DIRECTORY_2_RESULT = os.path.join(DIRECTORY_TOP, '2_result')

# run_setup_calibrate_picoscope.py
RE_CONFIG_SETUP = re.compile('run_setup_(?P<setup>.*?).py')

DEFINED_BY_MEASUREMENTS='DEFINED_BY_MEASUREMENTS'
DEFINED_BY_SETUP='DEFINED_BY_SETUP'

pp = pprint.PrettyPrinter(indent=2)

class MeasurementData:
  def __init__(self, configMeasurement, read=False):
    assert isinstance(configMeasurement, ConfigMeasurement)

    self.configMeasurement = configMeasurement
    self.list_overflow = []
    self.fA = None
    self.fD = None
    self.dt_s = None
    self.num_samples = None
    self.dictMinMax_V = {}

    if not read:
      return

    with open(self.configMeasurement.get_filename_data('txt'), 'r') as f:
      d = eval(f.read())
    self.dt_s = d['dt_s']
    self.num_samples = d['num_samples']
    self.list_overflow = d['list_overflow']

    self.channelA_volts_per_adu = d['channelA_volts_per_adu']
    self.channelD_volts_per_adu = d['channelD_volts_per_adu']

  def open_files(self, mode):
    assert mode in ('rb', 'wb')
    assert self.fA is None
    assert self.fD is None
    self.fA = open(self.configMeasurement.get_filename_data('a_bin'), mode)
    self.fD = open(self.configMeasurement.get_filename_data('d_bin'), mode)

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

  def __prepareGainPhase(self, i_start, i_end, points):
    a = self.dt_s * 2.0 * np.pi * self.configMeasurement.configFrequency.frequency_Hz
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

  def update_min_max(self, buf, channelA, test_max):
    assert isinstance(channelA, bool)
    assert isinstance(test_max, bool)
    key = f'channel{"A" if channelA else "D"}_{"max" if test_max else "min"}'

    f_V = self.dictMinMax_V.get(key, -1000.0 if test_max else 1000.0)
    if test_max:
      f_V = max(f_V, buf.max())
    else:
      f_V = min(f_V, buf.min())
    self.dictMinMax_V[key] = f_V

  def write(self):
    aux_data = dict(
      channelA_volts_per_adu = self.channelA_volts_per_adu,
      channelD_volts_per_adu = self.channelD_volts_per_adu,
      dt_s = self.dt_s,
      num_samples = self.num_samples,
      list_overflow = self.list_overflow,
    )

    with open(self.configMeasurement.get_filename_data('txt'), 'w') as f:
      pprint.pprint(aux_data, stream=f)

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

      self.update_min_max(bufA_V, channelA=True, test_max=True)
      self.update_min_max(bufA_V, channelA=True, test_max=False)
      self.update_min_max(bufD_V, channelA=False, test_max=True)
      self.update_min_max(bufD_V, channelA=False, test_max=False)
      
      i_end = i_start + len(bufA_V)
      self.__prepareGainPhase(i_start, i_end, points)
      complexA += self.__GainPhase(bufA_V)
      complexD += self.__GainPhase(bufD_V)
      i_start = i_end

    self.close_files()

    return complexA, complexD

  def condense_0to1(self):
    pass

  def dump_plot(self):
    # t = np.arange(-scope.pre_trigger, dt*num_samples-scope.pre_trigger, dt)
    
    # t = np.arange(0, self.dt_s*self.num_samples, self.dt_s)
    # plt.plot(t, self.channelA)
    if True:
      fig, ax = plt.subplots()

      def reduce(setup):
        x_points = 1000
        reduce_factor = len(setup)//x_points
        if reduce_factor < 1:
          reduce_factor = 1
        data = setup[::reduce_factor]
        return data

      lineA, = ax.plot(reduce(self.channelA), linewidth=0.1, color='blue')
      # lineA.set_label('Channel A')

      lineD, = ax.plot(reduce(self.channelD), linewidth=0.1, color='red')
      # lineD.set_label('Channel D')
      # lineD.set_dashes([2, 2, 10, 2])  # 2pt line, 2pt break, 10pt line, 2pt break

      ax.set_title(self.config)
      # ax.legend()

      filename_png = self.config.get_filename_data(extension='png', directory=DIRECTORY_1_CONDENSED)
      print(f'writing: {filename_png}')
      fig.savefig(filename_png)
      fig.clf()
      # plt.show()

    if False:
      plt.plot(self.channelD)
      plt.ylabel('channel D')
      plt.show()

class ConfigSetup:
  def __init__(self):
    self.skalierungsfaktor = DEFINED_BY_MEASUREMENTS
    self.input_Vp = DEFINED_BY_MEASUREMENTS
    self.input_set_Vp = DEFINED_BY_MEASUREMENTS
    self.setup_name = DEFINED_BY_SETUP
    self.diagram_legend = DEFINED_BY_SETUP
    self.result_gain = DEFINED_BY_SETUP
    self.result_unit = DEFINED_BY_SETUP
    self.reference = DEFINED_BY_SETUP

  def get_filename_data(self, extension, directory=DIRECTORY_0_RAW):
    filename = f'data_{self.setup_name}'
    return os.path.join(directory, f'{filename}.{extension}')

  def create_directories(self):
    for directory in (DIRECTORY_0_RAW, DIRECTORY_1_CONDENSED, DIRECTORY_2_RESULT):
        if not os.path.exists(directory):
          os.makedirs(directory)

  def _update_element(self, key, value):
    assert key in self.__dict__
    self.__dict__[key] = value

  def update_by_dict(self, dict_config_setup):
    for key, value in dict_config_setup.items():
      self._update_element(key, value)

  def update_by_channel_file(self, filename_channel):
    self.create_directories()
    dict_globals = {}
    with open(filename_channel) as f:
      exec(f.read(), dict_globals)
    dict_config_setup = dict_globals['dict_config_setup']
    self.update_by_dict(dict_config_setup)

    match = RE_CONFIG_SETUP.match(os.path.basename(filename_channel))
    assert match is not None
    setup_name = match.group('setup')
    self._update_element('setup_name', setup_name)

  def iterConfigMeasurements(self):
    import config_common
    for configFrequency in config_common.list_ConfigFrequency:
      yield ConfigMeasurement(self, configFrequency)

  def measure_for_all_frequencies(self, measured_only_first=False):
    picoscope = program_picoscope.PicoScope(self)
    picoscope.connect()
    for configMeasurement in self.iterConfigMeasurements():
      configMeasurement.measure(picoscope)
      if measured_only_first:
        return

  def condense_0to1_for_all_frequencies(self):
    for configMeasurement in self.iterConfigMeasurements():
      measurementData = MeasurementData(configMeasurement, read=True)
      measurementData.condense_0to1()

    start = time.time()
    list_result_1 = []

    for configMeasurement in self.iterConfigMeasurements():
      print(f'configMeasurement.configFrequency.frequency_Hz: {configMeasurement.configFrequency.frequency_Hz}')
      measurementData = MeasurementData(configMeasurement, read=True)
      complexA, complexD = measurementData.read()
      dict_data = dict(
        frequency_Hz=configMeasurement.configFrequency.frequency_Hz,
        list_overflow=measurementData.list_overflow,
        complexA=complexA,
        complexD=complexD,
      )
      dict_data.update(measurementData.dictMinMax_V)
      list_result_1.append(dict_data)
    print('Duration {}s'.format(time.time()-start))

    with open(configMeasurement.configSetup.get_filename_data('txt', DIRECTORY_1_CONDENSED), 'w') as f:
      pprint.pprint(list_result_1, stream=f)

  def condense_1to2(self):
    resultSetup = ResultSetup(self)
    resultSetup.pyplot()
    return resultSetup

class ResultSetup:
  def __init__(self, configSetup):
    self.configSetup = configSetup

    with open(self.configSetup.get_filename_data('txt', DIRECTORY_1_CONDENSED), 'r') as f:
      self.list_result_1 = eval(f.read())

    list_frequency = []
    list_complexA = []
    list_complexD = []
    for configMeasurement, result_1 in zip(self.configSetup.iterConfigMeasurements(), self.list_result_1):
      complexA=result_1['complexA']
      complexD=result_1['complexD']
      frequency_Hz=result_1['frequency_Hz']
      assert frequency_Hz == configMeasurement.configFrequency.frequency_Hz
      list_complexA.append(complexA)
      list_complexD.append(complexD)
      list_frequency.append(frequency_Hz)

    self.arr_frequency_Hz = np.array(list_frequency)
    self.arr_complexA = np.array(list_complexA)
    self.arr_complexD = np.array(list_complexD)
    self.arr_gainAD = self.arr_complexA/self.arr_complexD

  def pyplot(self):

    arr_Y = self.arr_gainAD.real
    fig, ax1 = plt.subplots()

    ax1.tick_params('y', colors='blue')
    ax1.ticklabel_format(useOffset=False)
    lineA, = ax1.plot(self.arr_frequency_Hz, arr_Y, linewidth=1.0, color='blue')
    lineA.set_label('m.complexA/m.complexD')

    fig.legend()
    filename_png = self.configSetup.get_filename_data('png', DIRECTORY_1_CONDENSED)
    print(f'writing: {filename_png}')
    fig.savefig(filename_png)
    # plt.show()
    plt.close()

class ConfigFrequency:
  def __init__(self, frequency_Hz):
    MINIMAL_DURATION_S = 0.1
    MAXIMAL_DURATION_S = 150.0
    PERIODS_SINE_OPTIMAL = 5.0
    self.frequency_Hz = frequency_Hz
    self.duration_s = 1.0 / frequency_Hz * PERIODS_SINE_OPTIMAL
    if self.duration_s > MAXIMAL_DURATION_S:
      self.duration_s = MAXIMAL_DURATION_S
    if self.duration_s < MINIMAL_DURATION_S:
      self.duration_s = MINIMAL_DURATION_S


def getConfigFrequencies(series='E6', minimal=100, maximal=1e3):
  frequencies_Hz = program_config_frequencies.eseries(series=series, minimal=minimal, maximal=maximal)

  # First the high frequencies, then low frequencies
  frequencies_Hz.sort(reverse=True)
  list_ConfigFrequency = list(map(ConfigFrequency, frequencies_Hz))
  return list_ConfigFrequency

class ConfigMeasurement:
  def __init__(self, configSetup, configFrequency):
    assert isinstance(configSetup, ConfigSetup)
    assert isinstance(configFrequency, ConfigFrequency)

    self.configSetup = configSetup
    self.configFrequency = configFrequency

  def __str__(self):
    return f'{self.configSetup.diagram_legend} ({self.configSetup.setup_name}, {self.configFrequency.frequency_Hz:012.2f}hz, {self.configFrequency.duration_s:0.3f}s)'
    return f'{self.configSetup.diagram_legend} ({self.configSetup.setup_name}, {self.configFrequency.frequency_Hz:0.0e}hz, {self.configFrequency.duration_s:0.0e}s)'

  def get_filename_data(self, extension, directory=DIRECTORY_0_RAW):
    filename = f'data_{self.configSetup.setup_name}_{self.configFrequency.frequency_Hz:012.2f}hz'
    # filename = f'data_{self.setup_name}_{self.frequency_Hz:0.2e}hz'
    # filename = f'data_{self.setup_name}_{self.frequency_Hz:012.2e}hz'
    # filename = f'data_{self.setup_name}_{self.frequency_Hz:06d}hz'
    return os.path.join(directory, f'{filename}.{extension}')
  
  def get_logfile(self, directory=DIRECTORY_0_RAW):
    return open(self.get_filename_data('log.txt', directory), 'w')

  def measure(self, picoscope):
    # picoscope.acquire(setup_name='ch1', frequency_hz=config.frequency_Hz, duration_s=config.duration_s, amplitude_Vpp=config.input_set_Vp)
    picoscope.acquire(self)

def get_configSetup_by_filename(config_setup_filename):
  import config_common
  config = ConfigSetup()
  config.update_by_dict(config_common.dict_config_setup_defaults)
  config.update_by_channel_file(config_setup_filename)
  return config

def get_configSetups():
  list_configs = []
  for filename in os.listdir(DIRECTORY_TOP):
    match = RE_CONFIG_SETUP.match(os.path.basename(filename))
    if match:
      list_configs.append(os.path.join(DIRECTORY_TOP, filename))
  return list_configs

def run_condense_0to1():
  print('get_configSetups: {}'.format(get_configSetups()))
  for configsetup_filename in get_configSetups():
    config = get_configSetup_by_filename(configsetup_filename)
    config.condense_0to1_for_all_frequencies()

class ResultCommon:
  def __init__(self):
    print('get_configSetups: {}'.format(get_configSetups()))
    self.list_resultSetup = []
    self.dict_resultSetupReference = {}
    for configsetup_filename in get_configSetups():
      config = get_configSetup_by_filename(configsetup_filename)
      resultSetup = config.condense_1to2()
      if config.reference == None:
        self.dict_resultSetupReference[config.setup_name] = resultSetup
      else:
        self.list_resultSetup.append(resultSetup)
  
  def plot(self):
    for resultSetup in self.list_resultSetup:
      resultSetupReference = self.dict_resultSetupReference[resultSetup.configSetup.reference]
      plot_for_one_setup(resultSetup, resultSetupReference)

def run_condense_1to2_result():
  resultCommon = ResultCommon()
  resultCommon.plot()

def plot_for_one_setup(resultSetup, resultSetupReference):
  assert isinstance(resultSetup, ResultSetup)
  assert isinstance(resultSetupReference, ResultSetup)

  arr_Y = (resultSetup.arr_gainAD / resultSetupReference.arr_gainAD).real

  fig, ax1 = plt.subplots()

  ax1.tick_params('y', colors='blue')
  ax1.ticklabel_format(useOffset=False)
  lineA, = ax1.plot(resultSetup.arr_frequency_Hz, arr_Y, linewidth=1.0, color='blue')
  lineA.set_label('m.complexA/m.complexD referenced')

  fig.legend()
  filename_png = resultSetup.configSetup.get_filename_data('png', DIRECTORY_2_RESULT)
  print(f'writing: {filename_png}')
  fig.savefig(filename_png)
  # plt.show()
  plt.close()

# class PyMeas2019:
#   def __init__(self):
#     for directory in (DIRECTORY_0_RAW, DIRECTORY_1_CONDENSED, DIRECTORY_2_RESULT):
#       if not os.path.exists(directory):
#         os.makedirs(directory)

#   print('get_configSetups: {}'.format(get_configSetups()))
#   for configsetup_filename in get_configSetups():
#     config = get_configSetup_by_filename(configsetup_filename)
#     config.condense_0to1_for_all_frequencies()

