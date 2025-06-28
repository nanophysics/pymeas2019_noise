import pathlib

from . import library_logger, run_1_condense, run_1_process_raw_0


def main():
    dir_measurement = pathlib.Path.cwd()

    library_logger.init_logger_condense(dir_measurement)
    run_1_process_raw_0.doit(dir_measurement=dir_measurement)
    run_1_condense.doit(dir_measurement=dir_measurement)

if __name__ == "__main__":
    main()
