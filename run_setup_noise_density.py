import program
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

__list_ConfigFrequency = program.getConfigFrequencies(series='E6', minimal=100.0, maximal=1000.0)

dict_config_setup = dict(
  diagram_legend = 'Measure Noise Density',
  list_frequency_Hz=__list_ConfigFrequency,
  input_Vp = PS5000ARange.R_5V,
  # input_Vp = PS5000ARange.R_10MV,
)

if __name__ == '__main__':
  configSetup = program.get_configSetup_by_filename(__file__)
  configSetup.measure_for_all_frequencies()
  pass
  configSetup.condense_0to1_for_all_frequencies()
  program.run_condense_1to2_result()
  