import program
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

dict_config_setup = dict(
  diagram_legend = 'Measure Noise Density',
  duration_s = 1.0,
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

  max_filesize_bytes = 5e9,
)

if __name__ == '__main__':
  configSetup = program.get_configSetup_by_filename(__file__)
  configSetup.measure_for_all_frequencies()
  pass
  configSetup.condense_0to1()
  program.run_condense_1to2_result()
  