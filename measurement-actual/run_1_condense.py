import pathlib

import library_path

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

DIR_MEASUREMENT = library_path.find_append_path()

# pylint: disable=wrong-import-position
import library_logger
import program
import run_2_composite_plots


def reload_if_changed(dir_raw):
    return program.reload_if_changed(dir_raw=dir_raw)


def run():
    library_logger.init_logger_condense(DIRECTORY_OF_THIS_FILE)

    program.run_condense(DIR_MEASUREMENT)
    run_2_composite_plots.run()


if __name__ == "__main__":
    run()
