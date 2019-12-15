import program
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

dict_config_setup = dict(
  diagram_legend = 'Measure Noise Density',
  input_channel = 'A',
  skalierungsfaktor = 1.0E-3,   # Amplifier Gain 1000   todoPeter spaeter korrrekt einbauen
  # input_Vp = PS5000ARange.R_10MV,
  # input_Vp = PS5000ARange.R_20MV,
  # input_Vp = PS5000ARange.R_50MV,
  input_Vp = PS5000ARange.R_100MV,
  # input_Vp = PS5000ARange.R_200MV,
  # input_Vp = PS5000ARange.R_500MV,
  # input_Vp = PS5000ARange.R_1V,
  # input_Vp = PS5000ARange.R_2V,
  # input_Vp = PS5000ARange.R_5V,
  # input_Vp = PS5000ARange.R_10V,
  # input_Vp = PS5000ARange.R_20V,
  # input_Vp = PS5000ARange.R_50V, 
  bandwitdth = 'BW_20MHZ',
  offset = 0.0,
  resolution = '16bit',
  # duration_s = 0.1,
  # dt_s = 1.6e-08,
  duration_s = 1.0,
  dt_s = 1.6e-07,
  # dt_s = None,

  max_filesize_bytes = 5e9,
)

if __name__ == '__main__':
  # import program_fir
  # thread = program_fir.DensityPlot.directory_plot_thread(program.DIRECTORY_1_CONDENSED)
  configSetup = program.get_configSetup_by_filename(__file__)
  configSetup.measure_for_all_frequencies()
  # import time
  # time.sleep(10.0)
  # thread.stop()
  pass
  # configSetup.condense_0to1()
  # program.run_condense_1to2_result()
  