dict_config = dict(
  diagram_legend = 'CH1 common mode mess',
  input_Vp = 2.0,
)

if __name__ == '__main__':
  import program
  configuration = program.get_config_by_config_filename(__file__)
  configuration.measure_for_all_frequencies()
  pass
