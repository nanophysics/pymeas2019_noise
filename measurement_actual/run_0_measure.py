import config_measurement  # pylint: disable=wrong-import-position
import library_path
from pymeas2019_noise import program_measure

library_path.init(__file__)

if __name__ == "__main__":
    configsetup = config_measurement.get_configsetup()
    configsetup.validate()
    program_measure.measure(configsetup, dir_measurement=library_path.DIR_MEASUREMENT)
