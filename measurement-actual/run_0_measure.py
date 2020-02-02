import math

import library_path
dir_measurement = library_path.find_append_path()

import program
try:
  from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange
except ImportError:
  import enum
  class PS5000ARange(enum.IntEnum):
    R_100MV = 3

# sample frequencies and fir_counts
f0_fast_fs_hz = 125E6 # do not change this values as this is the fastest rate with 15 bit
f1_medium_fs_hz = f0_fast_fs_hz / float(2**1)  # do not change this values as this is the fastest rate with 16 bit
exponent_slow = 5 # free to change. Peter has choosen 5 on his laptop
f2_slow_fs_hz = f0_fast_fs_hz/ float(2**exponent_slow)
f1_medium_useful_hz = 20E6 / 3.0 # 3 dB frequency is 20 Mhz
#print(f'f1_medium_useful_hz wanted  : {f1_medium_useful_hz:.0f} Hz')
temp = int(round( math.log(f0_fast_fs_hz / f1_medium_useful_hz,2)))
f1_medium_useful_hz = f0_fast_fs_hz / 2**temp
#print(f'f1_medium_useful_hz selected: {f1_medium_useful_hz:.0f} Hz')
f0_fast_fir_count_skipped = 0 # fixed: we do not want to skip any. Due to nyquist criterion we could see some spurious signals for frequencies above. 
f0_fast_fir_count = int(round( math.log(f0_fast_fs_hz / f1_medium_useful_hz,2)))
# input B filter
R_filter_input_B_ohm = 10000.0
C_filter_input_B_farad = 1e-9
fg_filter_input_B = 1.0 / ( 2.0 * math.pi * R_filter_input_B_ohm * C_filter_input_B_farad)
#print(f'fg_filter_input_B: {fg_filter_input_B:.0f} Hz')
f2_slow_useful_hz = fg_filter_input_B / 3.0
#print(f'f2_slow_useful_hz wanted  : {f2_slow_useful_hz:.0f} Hz')
f1_medium_fir_count = int( round(math.log(f1_medium_fs_hz / f2_slow_useful_hz,2)))
f2_slow_useful_hz = f1_medium_fs_hz / 2**f1_medium_fir_count
f1_medium_fir_count_skipped = int(round(math.log(f1_medium_fs_hz / f1_medium_useful_hz,2)))
#print(f'f2_slow_useful_hz selected  : {f2_slow_useful_hz:.0f} Hz')
f2_slow_fir_count_skipped = int(round(math.log(f2_slow_fs_hz / f2_slow_useful_hz,2)))
fir_count_2_slow = f2_slow_fir_count_skipped + 27 # free to choose

dict_config_setup = dict(
  setup_name = 'Measure Noise Density',
  # input_Vp = PS5000ARange.R_10MV,
  # input_Vp = PS5000ARange.R_20MV,
  # input_Vp = PS5000ARange.R_50MV,
  # input_Vp = PS5000ARange.R_100MV,
  # input_Vp = PS5000ARange.R_200MV,
  # input_Vp = PS5000ARange.R_500MV,
  # input_Vp = PS5000ARange.R_1V,
  # input_Vp = PS5000ARange.R_2V,
  # input_Vp = PS5000ARange.R_5V,
  # input_Vp = PS5000ARange.R_10V,
  # input_Vp = PS5000ARange.R_20V,
  # input_Vp = PS5000ARange.R_50V, 

  steps = ( 
    dict(
      stepname = '0_fast',
      # External
      skalierungsfaktor = 1.0E-3,
      # Processing
      fir_count = f0_fast_fir_count,
      fir_count_skipped = f0_fast_fir_count_skipped, # highest frequencies get skipped
      # Picoscope
      input_channel = 'A', # channel A is connected without filter to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_FULL',
      offset = 0.0,
      resolution = '15bit',
      duration_s = 2.0,
      dt_s = 1.0 / f0_fast_fs_hz,
    ),
    dict(
      stepname = '1_medium',
      # External
      skalierungsfaktor = 1.0E-3,
      # Processing
      fir_count = f1_medium_fir_count,
      fir_count_skipped = f1_medium_fir_count_skipped,
      # Picoscope
      input_channel = 'A', # channel A is connected without filter to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_20MHZ',
      offset = 0.0,
      resolution = '16bit',
      duration_s = 2.0,
      dt_s = 1.0 / f1_medium_fs_hz,
    ),
    dict(
      stepname = '2_slow',
      # External
      skalierungsfaktor = 1.0E-3,
      # Processing
      fir_count = fir_count_2_slow,
      fir_count_skipped = f2_slow_fir_count_skipped,
      # Picoscope
      input_channel = 'B', # channel B is connected with filter low pass 100 kHz ??? to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_20MHZ',
      offset = 0.0,
      resolution = '16bit',
      duration_s = 600.0,
      #duration_s = 7*3600.0,
      dt_s = 1 / f2_slow_fs_hz,
    ),
  )
)
print (dict_config_setup)

def run():
  # import program_fir
  # thread = program_fir.DensityPlot.directory_plot_thread(program.DIRECTORY_0_RAW, program.DIRECTORY_1_CONDENSED)
  configSetup = program.get_configSetup_by_filename(dict_config_setup)

  configSetup.measure_for_all_steps(dir_measurement, start_animation=True)
  program.run_condense(dir_measurement)

  # import time
  # time.sleep(10.0)
  # thread.stop()

  # import program_fir
  # program_fir.DensityPlot.directory_plot(program.DIRECTORY_0_RAW, program.DIRECTORY_1_CONDENSED)
  pass
  # configSetup.condense_0to1()
  # program.run_condense_1to2_result()

  import run_1_condense
  run_1_condense.run()

if __name__ == '__main__':
  run()
