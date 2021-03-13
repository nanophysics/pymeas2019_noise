import library_path

library_path.init(__file__)

import config_measurement  # pylint: disable=wrong-import-position

# pylint: disable=wrong-import-position
from pymeas import program_measure

if __name__ == "__main__":
    configsetup = config_measurement.get_configsetup()
    configsetup.validate()
    program_measure.measure(configsetup, dir_measurement=library_path.DIR_MEASUREMENT)
