TITLE = 'Preamplifier Noise 2020: Measure Noise Density'

def get_dict_config_setup():
  import program_picoscope
  dict_config_setup = program_picoscope.get_config_setupPS500A(
    # To choose the best input range, see the description in 'program_picoscope'.
    inputRange=program_picoscope.InputRange.R_100mV,
    duration_slow_s=48*3600.0,
    skalierungsfaktor=1.0E-3
  )
  return dict_config_setup
