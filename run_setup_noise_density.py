import program
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

freq = program.ConfigFrequency(1000.0)
freq.duration_s = 2.0

dict_config_setup = dict(
  diagram_legend = 'Measure Noise Density',
  list_frequency_Hz = [freq,],
  input_set_Vp=0.0, # We don't need the frequency-output. Set voltage input, out is adjusted automatically
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
  