#
# Make sure that the subrepos are included in the python path
#
import gc
import re
import os
import sys
import math
import time
import cmath
import pprint
import logging
import pathlib
import itertools

TOPDIR=pathlib.Path(__file__).parent.absolute()
MSL_EQUIPMENT_PATH = TOPDIR.joinpath('libraries/msl-equipment')
assert MSL_EQUIPMENT_PATH.joinpath('README.rst').is_file(), f'Subrepo is missing (did you clone with --recursive?): {MSL_EQUIPMENT_PATH}'
sys.path.insert(0, str(MSL_EQUIPMENT_PATH))

try:
  import msl.loadlib
  import numpy as np
  import matplotlib.pyplot as plt
except ImportError as ex:
  print(f'ERROR: Failed to import ({ex}). Try: pip install -r requirements.txt')
  sys.exit(0)

import library_plot
import program_fir

import program_picoscope_5442D as program_picoscope

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

DIRECTORY_TOP = os.path.dirname(os.path.abspath(__file__))
DIRECTORY_RESULT = 'result'

DEFINED_BY_SETUP='DEFINED_BY_SETUP'

pp = pprint.PrettyPrinter(indent=2)

class MeasurementDataObsolete:
  def __init__(self, configSetup, read=False):
    assert isinstance(configSetup, ConfigSetup)

    self.configSetup = configSetup
    self.list_overflow = []
    self.fA = None
    self.dt_s = None
    self.num_samples = None
    self.dictMinMax_V = {}

    if not read:
      return

    with open(self.configSetup.get_filename_data('txt'), 'r') as f:
      d = eval(f.read())
    self.dt_s = d['dt_s']
    self.num_samples = d['num_samples']
    self.list_overflow = d['list_overflow']

    self.channelA_volts_per_adu = d['channelA_volts_per_adu']

  def open_files(self, mode):
    assert mode in ('rb', 'wb')
    assert self.fA is None
    self.fA = open(self.configSetup.get_filename_data('a_bin'), mode)

  def close_files(self):
    assert self.fA is not None
    self.fA.close()
    self.fA=None

  def write(self):
    aux_data = dict(
      channelA_volts_per_adu = self.channelA_volts_per_adu,
      dt_s = self.dt_s,
      num_samples = self.num_samples,
      list_overflow = self.list_overflow,
    )

    with open(self.configSetup.get_filename_data('txt'), 'w') as f:
      pprint.pprint(aux_data, stream=f)

  # def read(self):
  #   self.open_files('rb')

  #   # See: msl-equipment\msl\equipment\resources\picotech\picoscope\channel.py
  #   # np.empty((0, 0), dtype=np.int16)
  #   bytes_per_sample = 2

  #   data_bytes = self.fA.read(bytes_per_sample*self.num_samples)
  #   rawA = np.frombuffer(data_bytes, dtype=np.int16)
  #   bufA_V = self.channelA_volts_per_adu * rawA
  #   assert self.num_samples == len(bufA_V)

  #   self.close_files()

  #   return bufA_V



    # ds = DensitySummary(self.list_density, config=self.config, directory=self.directory_condensed)
    # ds.plot()

    print(f'Duration {time.time()-start:0.2f}')

    # bufA_V = self.read()
    # self.dump_sub(bufA_V, 0.001)

  # def dump_sub(self, bufA_V, time_s):
  #   samples = int(time_s/self.dt_s)
  #   print(f'self.dt_s={self.dt_s:.4e} / f={1.0/self.dt_s:.4e} -> samples={self.num_samples}, t_s={self.num_samples*self.dt_s}')
  #   print(f'time_s={time_s:.4e} -> samples={samples}')
  #   a = bufA_V[0:samples]
  #   plt.plot(a)
  #   plt.ylabel('V')
  #   plt.show()

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

      lineB, = ax.plot(reduce(self.channelB), linewidth=0.1, color='red')
      # lineB.set_label('Channel B')
      # lineB.set_dashes([2, 2, 10, 2])  # 2pt line, 2pt break, 10pt line, 2pt break

      ax.set_title(self.config)
      # ax.legend()

      filename_png = self.config.get_filename_data(extension='png', directory=DIRECTORY_1_CONDENSED)
      print(f'writing: {filename_png}')
      fig.savefig(filename_png)
      fig.clf()
      # plt.show()

    if False:
      plt.plot(self.channelA)
      plt.ylabel('channel B')
      plt.show()

class ConfigStep:
  def __init__(self, dict_values={}):
    self.stepname = DEFINED_BY_SETUP
    self.fir_count = DEFINED_BY_SETUP
    self.fir_count_skipped = DEFINED_BY_SETUP
    self.input_Vp = DEFINED_BY_SETUP
    self.skalierungsfaktor = DEFINED_BY_SETUP
    self.input_channel = DEFINED_BY_SETUP
    self.duration_s = DEFINED_BY_SETUP
    self.diagram_legend = DEFINED_BY_SETUP
    self.result_gain = DEFINED_BY_SETUP
    self.result_unit = DEFINED_BY_SETUP
    self.reference = DEFINED_BY_SETUP
    self.bandwitdth = DEFINED_BY_SETUP
    self.offset = DEFINED_BY_SETUP
    self.resolution = DEFINED_BY_SETUP
    self.dt_s = DEFINED_BY_SETUP

    self.update_by_dict(dict_values)

  def _update_element(self, key, value):
    assert key in self.__dict__
    self.__dict__[key] = value

  def update_by_dict(self, dict_config_setup):
    for key, value in dict_config_setup.items():
      self._update_element(key, value)

class ConfigSetup:
  def __init__(self):
    self.diagram_legend = DEFINED_BY_SETUP
    self.setup_name = DEFINED_BY_SETUP
    self.steps = DEFINED_BY_SETUP

  # def get_filename_data(self, extension, directory=DIRECTORY_0_RAW):
  #   filename = f'data_{self.setup_name}'
  #   return os.path.join(directory, f'{filename}.{extension}')

  # def create_directories(self):
  #   for directory in (DIRECTORY_0_RAW, DIRECTORY_1_CONDENSED, DIRECTORY_2_RESULT):
  #       if not os.path.exists(directory):
  #         os.makedirs(directory)

  def delete_directory_contents(self, directory):
    for filename in os.listdir(directory):
      os.remove(os.path.join(directory, filename))

  def _update_element(self, key, value):
    assert key in self.__dict__
    if key == 'steps':
      self.__dict__[key] = [ConfigStep(v) for v in value]
      return
    self.__dict__[key] = value

  def update_by_dict(self, dict_config_setup):
    for key, value in dict_config_setup.items():
      self._update_element(key, value)

  def update_by_channel_file(self, dict_config_setup):
    self.update_by_dict(dict_config_setup)

  def measure_for_all_steps(self, dir_measurement):
    dir_results = dir_measurement.joinpath(library_plot.ResultAttributes.result_dir_actual())
    if dir_results.exists():
      self.delete_directory_contents(str(dir_results))
    else:
      dir_results.mkdir()

    for configStep in self.steps:
      picoscope = program_picoscope.PicoScope(configStep)
      picoscope.connect()
      sample_process = program_fir.SampleProcess(program_fir.SampleProcessConfig(configStep), str(dir_results))
      picoscope.acquire(configStep, sample_process.output)
      picoscope.close()


def get_configSetup_by_filename(dict_config_setup):
  import config_common
  config = ConfigSetup()
  config.update_by_dict(config_common.dict_config_setup_defaults)
  config.update_by_channel_file(dict_config_setup)
  return config

def get_configSetups():
  list_configs = []
  for filename in os.listdir(DIRECTORY_TOP):
    match = RE_CONFIG_SETUP.match(os.path.basename(filename))
    if match:
      list_configs.append(os.path.join(DIRECTORY_TOP, filename))
  return list_configs

def run_plot(dir_measurement):
  # if False:
  #   import cProfile
  #   cProfile.run('program.run_condense_0to1()', sort='tottime')
  #   import sys
  #   sys.exit(0)
  dir_result = dir_measurement.joinpath(DIRECTORY_RESULT)
  if not dir_result.exists():
    dir_result.mkdir()

  for dir_raw in dir_measurement.glob(library_plot.ResultAttributes.RESULT_DIR_PATTERN):
    if not dir_raw.is_dir():
      continue
    resultAttributes = library_plot.ResultAttributes(dir_raw=dir_raw)
    run_condense_0to1(resultAttributes=resultAttributes, trace=False)
    run_condense_0to1(resultAttributes=resultAttributes, trace=True)
    pass
    # import program_fir
    # program_fir.DensityPlot.directory_plot(program.DIRECTORY_0_RAW, program.DIRECTORY_1_CONDENSED)
    pass

def run_condense_0to1(resultAttributes, trace=False):
  list_density = list(program_fir.DensityPlot.plots_from_directory(dir_input=resultAttributes.dir_raw, skip=not trace))

  ds = program_fir.DensitySummary(list_density, directory=resultAttributes.dir_raw, trace=trace)
  ds.write_summary_file(trace=trace)
  if not trace:
    ds.write_summary_pickle()

  file_tag = '_trace' if trace else ''
  ds.plot(file_tag=file_tag, color_given='blue')

  if not trace:
    file_tag = '_colors'
    ds.plot(file_tag=file_tag)

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

