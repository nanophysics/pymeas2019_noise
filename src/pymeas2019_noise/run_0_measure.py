import pathlib

import config_measurement

from . import program_measure

if __name__ == "__main__":
    configsetup = config_measurement.get_configsetup()
    configsetup.validate()
    program_measure.measure(configsetup, dir_measurement=pathlib.Path.cwd())
