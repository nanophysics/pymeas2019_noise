import library_path

dir_measurement = library_path.find_append_path()

import program  # pylint: disable=wrong-import-position
import run_2_composite_plots  # pylint: disable=wrong-import-position


def reload_if_changed(dir_raw):
    return program.reload_if_changed(dir_raw=dir_raw)


def run():
    library_path.init_logger_condense()

    program.run_condense(dir_measurement)
    run_2_composite_plots.run()


if __name__ == "__main__":
    run()
