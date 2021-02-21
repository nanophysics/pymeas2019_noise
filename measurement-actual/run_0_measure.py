import library_path
import config_measurement

TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()


# pylint: disable=wrong-import-position
from pymeas import program_measure

if __name__ == "__main__":
    configsetup = config_measurement.get_configsetup()
    configsetup.validate()
    program_measure.measure(configsetup, dir_measurement=DIR_MEASUREMENT)
