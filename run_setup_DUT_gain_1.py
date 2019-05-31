from msl.equipment.resources.picotech.picoscope.enums import PS5000Range

dict_config_setup = dict(
  diagram_legend = 'Gain 1 of DUT',
  input_Vp = PS5000Range.R_20MV,
)

if __name__ == '__main__':
  import program
  configSetup = program.get_configSetup_by_filename(__file__)
  configSetup.measure_for_all_frequencies()
  pass
