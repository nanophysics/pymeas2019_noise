import pathlib

from . import program_measure


def main(subdir_raw: str):
    import config_measurement

    configsetup = config_measurement.get_configsetup()
    configsetup.validate()
    program_measure.measure(
        configsetup=configsetup,
        dir_measurement=pathlib.Path.cwd(),
        subdir_raw=subdir_raw,
    )


if __name__ == "__main__":
    main(subdir_raw="raw-blue-2026-05-24_19-33-12")
