from msl.equipment.resources.picotech.picoscope.enums import PS5000Range

dict_config = dict(
  diagram_legend = 'CH1 common mode mess',
  # input_Vp = PS5000Range.R_2V,
  input_Vp = PS5000Range.R_10MV,
)

if __name__ == '__main__':
  import program
  configuration = program.get_config_by_config_filename(__file__)
  configuration.measure_for_all_frequencies()
  pass
  program.run_condense_0_to_1()
