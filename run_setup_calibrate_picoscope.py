from msl.equipment.resources.picotech.picoscope.enums import PS5000Range

dict_config_setup = dict(
  diagram_legend = 'Calibrate Picoscope channel A versus D',
  input_Vp = PS5000Range.R_5V,
  # input_Vp = PS5000Range.R_10MV,
)

if __name__ == '__main__':
  import program
  configSetup = program.get_configSetup_by_filename(__file__)
  configSetup.measure_for_all_frequencies()
  pass
  program.run_condense_0to1()
