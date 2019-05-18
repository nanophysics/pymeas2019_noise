dict_config = dict(
  diagram_legend = 'CH2 common mode mess',
  input_Vp = 0.2,
)

if __name__ == '__main__':
  import program
  configuration = program.get_config_by_config_filename(__file__)
  configuration.measure_for_all_frequencies()
  pass
