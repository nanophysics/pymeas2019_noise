import config_measurement
from pymeas2019_noise import program_measure

if __name__ == "__main__":
    configsetup = config_measurement.get_configsetup()
    configsetup.validate()
    program_measure.measure0(configsetup, file=__file__)
