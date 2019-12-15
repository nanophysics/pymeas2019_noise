import program
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange


# .Waiting for thread 0.033Hz
# Done
# The sampling interval is 3.360000e-07 seconds, requested 3.333333e-07 seconds
# PicoScope5000A<Pico Technology|5442D| at SDK::ps5000a> PICO_SIG_GEN_PARAM: Incorrect parameter passed to signal generator.
# Traceback (most recent call last):
#   File "run_config_ch1.py", line 12, in <module>
#     configSetup.measure_for_all_steps()
#   File "C:\Projekte\ETH-Compact\versuche_picoscope\pymeas2019\program.py", line 239, in measure_for_all_steps
#     picoscope.acquire(config)
#   File "C:\Projekte\ETH-Compact\versuche_picoscope\pymeas2019\program_picoscope_5442D.py", line 65, in acquire
#     self.scope.set_sig_gen_builtin_v2(start_frequency=config.frequency_Hz, wave_type='sine', pk_to_pk=pk_to_pk, sweeps=0)
#   File "c:\projekte\eth-compact\versuche_picoscope\msl-equipment\msl\equipment\resources\picotech\picoscope\picoscope_api.py", line 962, in set_sig_gen_builtin_v2
#     trig_typ, trig_source, ext_in_threshold)
#   File "c:\projekte\eth-compact\versuche_picoscope\msl-equipment\msl\equipment\resources\picotech\picoscope\picoscope_api.py", line 73, in errcheck_api
#     self.raise_exception('{}: {}'.format(error_name, error_msg))
#   File "c:\projekte\eth-compact\versuche_picoscope\msl-equipment\msl\equipment\connection.py", line 88, in raise_exception
#     raise self._exception_handler('{!r}\n{}'.format(self, msg))
# msl.equipment.exceptions.PicoTechError: PicoScope5000A<Pico Technology|5442D| at SDK::ps5000a>
# PICO_SIG_GEN_PARAM: Incorrect parameter passed to signal generator.

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

dict_config_setup_defaults = dict(
  diagram_legend = 'dummyname',
  steps = (),
)
