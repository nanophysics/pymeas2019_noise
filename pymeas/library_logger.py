import logging
import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

LOGGER_NAME = "logger"
logger = logging.getLogger(LOGGER_NAME)


class Dummy:
    INITIALIZED = False


def init_logger_gui(directory):
    init_logger(directory, ("logger_gui.txt", "logger_gui_clone1.txt", "logger_gui_clone2.txt"))


def init_logger_condense(directory):
    init_logger(directory, ("logger_condense.txt", "logger_condense_1.txt", "logger_condense_2.txt"))


def init_logger_composite_plots(directory):
    init_logger(directory, ("logger_composite_plots.txt", "logger_composite_plots_1.txt", "logger_composite_plots_2.txt"))


def init_logger_measurement(directory):
    assert isinstance(directory, (type(None), pathlib.Path))
    if directory is None:
        directory = DIRECTORY_OF_THIS_FILE
    init_logger(directory, ("logger_measurement.txt",))


def init_logger_append(filename):
    print(f"logging to {str(filename)}")
    logger.setLevel(logging.INFO)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(filename=filename)
    fh.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)


def init_logger(directory, filenames):
    assert isinstance(directory, pathlib.Path)
    assert isinstance(filenames, (list, tuple))

    if Dummy.INITIALIZED:
        logger.warning("Logger already initialized")
        return
    Dummy.INITIALIZED = True

    for _filename in filenames:
        filename = directory / _filename
        if filename.exists():
            try:
                filename.unlink()
                break
            except PermissionError:
                # The file is already locked, try the next one
                continue
        break
    else:
        raise Exception(f"All log-files locked: {filenames}")

    init_logger_append(filename=filename)
