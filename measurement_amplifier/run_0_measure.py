import math
import program
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange


# Peter frequencies and fir_counts
f_sample_0_fast_hz = 125E6 # do not change this values as this is the fastest rate with 15 bit
f_sample_1_medium_hz = f_sample_0_fast_hz / float(2**1)  # do not change this values as this is the fastest rate with 16 bit
assert(( f_sample_1_medium_hz - 62.5E6) < 0.01 )
exponent_slow = 5 # free to change. Peter has choosen 9 on his laptop
f_sample_2_slow_hz = f_sample_0_fast_hz/ float(2**exponent_slow)
# todo: assert falls f_sample_2_slow_hz nicht in reihe der möglichen frequenzen passt

# 0_fast
reserve_fir_count_0_fast = 0 # fixed: we do not want to sip any
additional_fir_count_0_fast = 5 # we need to go to well below 20 MHz as bandwith of 1_medium is limited at 20 MHz
fir_count_0_fast = int( math.log(f_sample_0_fast_hz / f_sample_1_medium_hz,2) +  reserve_fir_count_0_fast + additional_fir_count_0_fast)
assert((f_sample_0_fast_hz / 2**fir_count_0_fast) < 20E6 *0.5 ) # well below 20 Mhz

# 1_medium
reserve_fir_count_1_medium = 6 # high enough to start below 20 Mhz
fir_count_1_medium = int( math.log(f_sample_1_medium_hz / f_sample_2_slow_hz,2) +  reserve_fir_count_1_medium)
assert(f_sample_1_medium_hz / 2**reserve_fir_count_1_medium < 20E6 *0.5)

# 2_slow
reserve_fir_count_2_slow = 5 # high enough to skip filter at input with low pass frequency of ???
fir_count_2_slow = reserve_fir_count_2_slow + 27 # free to choose
assert(fir_count_2_slow > reserve_fir_count_2_slow)

dict_config_setup = dict(
  diagram_legend = 'Measure Noise Density',
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
      skalierungsfaktor = 1.0E-3,   # Amplifier Gain 1000   todoPeter spaeter korrrekt einbauen
      # Processing
      fir_count = fir_count_0_fast,
      fir_count_skipped = reserve_fir_count_0_fast, # highest frequencies get skipped
      # Picoscope
      input_channel = 'A', # channel A is connected without filter to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_FULL',
      offset = 0.0,
      resolution = '15bit',
      duration_s = 2.0,
      dt_s = 1.0 /f_sample_0_fast_hz,
    ),
    dict(
      stepname = '1_medium',
      # External
      skalierungsfaktor = 1.0E-3,   # Amplifier Gain 1000   todoPeter spaeter korrrekt einbauen
      # Processing
      fir_count = fir_count_1_medium,
      fir_count_skipped = reserve_fir_count_1_medium,
      # Picoscope
      input_channel = 'A', # channel A is connected without filter to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_20MHZ',
      offset = 0.0,
      resolution = '16bit',
      duration_s = 2.0,
      dt_s = 1.0 / f_sample_1_medium_hz,
    ),
      dict(
      stepname = '2_slow',
      # External
      skalierungsfaktor = 1.0E-3,   # Amplifier Gain 1000   todoPeter spaeter korrrekt einbauen
      # Processing
      fir_count = fir_count_2_slow,
      fir_count_skipped = reserve_fir_count_2_slow,
      # Picoscope
      input_channel = 'B', # channel B is connected with filter low pass 100 kHz ??? to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_20MHZ',
      offset = 0.0,
      resolution = '16bit',
      duration_s = 60.0,
      #duration_s = 7*3600.0,
      dt_s = 1 / f_sample_2_slow_hz,
    ),
  )
)
#print ( dict_config_setup)

if __name__ == '__main__':
  # import program_fir
  # thread = program_fir.DensityPlot.directory_plot_thread(program.DIRECTORY_0_RAW, program.DIRECTORY_1_CONDENSED)
  configSetup = program.get_configSetup_by_filename(__file__)

  configSetup.measure_for_all_steps()
  # import time
  # time.sleep(10.0)
  # thread.stop()

  import program_fir
  # program_fir.DensityPlot.directory_plot(program.DIRECTORY_0_RAW, program.DIRECTORY_1_CONDENSED)
  pass
  # configSetup.condense_0to1()
  # program.run_condense_1to2_result()
  