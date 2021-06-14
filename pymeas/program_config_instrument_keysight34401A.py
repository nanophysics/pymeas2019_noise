import logging

from . import program_instrument_keysight34401A
from .program_configsetup import ConfigSetupKeysight34401A, ConfigStepKeysight34401A, InputRangeKeysight34401A

logger = logging.getLogger("logger")


def get_config_setupKeysight34401A():  # pylint: disable=too-many-statements
    setup = ConfigSetupKeysight34401A()
    setup.setup_name = "Measure"
    setup.module_instrument = program_instrument_keysight34401A

    step = ConfigStepKeysight34401A()
    step.stepname = "3_slow"
    step.skalierungsfaktor = 1.0
    step.input_Vp = InputRangeKeysight34401A.RANGE_100V  # RANGE_100mV, RANGE_1V, RANGE_10V, RANGE_100V, RANGE_1000V
    # Processing
    step.fir_count = 26
    step.fir_count_skipped = 0
    step.duration_s = 300.0
    step.dt_s = 0.02
    setup.step_3_slow = step

    return setup
