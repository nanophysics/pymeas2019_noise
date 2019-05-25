import helpers
from msl.equipment.resources.picotech.picoscope.enums import PS5000Range

frequencies_Hz = helpers.eseries(series='E6', minimal=100, maximal=1e6)
list_measurements = helpers.get_list_measurements(frequencies_Hz)

# list_measurements = (
#   dict(frequency_Hz=50, duration_s=1e0),
#   dict(frequency_Hz=1000, duration_s=1e-1),
#   dict(frequency_Hz=2000, duration_s=1e-1),
#   dict(frequency_Hz=5000, duration_s=1e-1),
#   dict(frequency_Hz=10000, duration_s=1e-2),
# )

# class PS5000Range(IntEnum):
#     R_10MV  = 0
#     R_20MV  = 1
#     R_50MV  = 2
#     R_100MV = 3
#     R_200MV = 4
#     R_500MV = 5
#     R_1V    = 6
#     R_2V    = 7
#     R_5V    = 8
#     R_10V   = 9
#     R_20V   = 10
#     R_50V   = 11
#     R_MAX   = 12

dict_config = dict(
  skalierungsfaktor=1.0,
  input_Vp=PS5000Range.R_2V,
  input_set_Vp=2.0, # set voltage input, out is adjusted automatically
  with_channel_D=True,
)
