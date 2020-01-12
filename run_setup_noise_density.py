import program
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

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
      fir_count = 8,
      fir_count_skipped = 4,
      # Picoscope
      input_channel = 'A', # channel A is connected without filter to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_FULL',  # spaeter BW_FULL
      offset = 0.0,
      resolution = '15bit',
      duration_s = 2.0,
      dt_s = 1.0 / 125E6,
    ),
    dict(
      stepname = '1_medium',
      # External
      skalierungsfaktor = 1.0E-3,   # Amplifier Gain 1000   todoPeter spaeter korrrekt einbauen
      # Processing
      fir_count = 8,
      fir_count_skipped = 4,
      # Picoscope
      input_channel = 'A', # channel A is connected without filter to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_20MHZ',
      offset = 0.0,
      resolution = '16bit',
      duration_s = 2.0,
      dt_s = 1.0 / 62.5E6,
    ),
    dict(
      stepname = '2_slow',
      # External
      skalierungsfaktor = 1.0E-3,   # Amplifier Gain 1000   todoPeter spaeter korrrekt einbauen
      # Processing
      fir_count = 15,
      fir_count_skipped = 4,
      # Picoscope
      input_channel = 'B', # channel B is connected with filter low pass 100 kHz ??? to the amplifier out
      input_Vp = PS5000ARange.R_100MV,
      bandwitdth = 'BW_20MHZ',
      offset = 0.0,
      resolution = '16bit',
      duration_s = 100.0,
      # dt_s = 1.6e-07,
      dt_s = 1 / 1E6,
    ),
  )
)

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
  