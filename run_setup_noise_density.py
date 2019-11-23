import program
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

dict_config_setup = dict(
  diagram_legend = 'Measure Noise Density',
  duration_s = 1.0,
  input_Vp = PS5000ARange.R_5V,
  # input_Vp = PS5000ARange.R_10MV,
  max_filesize_bytes = 10e9,
)

if __name__ == '__main__':
  configSetup = program.get_configSetup_by_filename(__file__)
  configSetup.measure_for_all_frequencies()
  pass
  configSetup.condense_0to1_for_all_frequencies()
  program.run_condense_1to2_result()
  