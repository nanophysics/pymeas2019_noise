from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

dict_config_setup = dict(
  diagram_legend = 'Gain 1 of DUT',
  input_Vp = PS5000ARange.R_5V,
  reference = 'calibrate_picoscope' # run_setup_calibrate_picoscope.py
)

if __name__ == '__main__':
  import program
  configSetup = program.get_configSetup_by_filename(__file__)
  configSetup.measure_for_all_frequencies()
  pass
  configSetup.condense_0to1_for_all_frequencies()
  program.run_condense_1to2_result()
