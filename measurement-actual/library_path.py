import sys
import pathlib
import logging

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()

LOGGER_NAME = "logger"
logger = logging.getLogger(LOGGER_NAME)


def find_append_path():
    dir_measurement = DIRECTORY_OF_THIS_FILE
    for parent in dir_measurement.parents:
        if (parent / "TOPDIR.TXT").exists():
            sys.path.insert(0, str(parent))
            return dir_measurement
    raise Exception('No file "TOPDIR.TXT" not found in parent directories!')


class Dummy:
    INITIALIZED = False


def init_logger_gui():
    init_logger(DIRECTORY_OF_THIS_FILE / "logger_gui.txt")


def init_logger_measurement():
    init_logger(DIRECTORY_OF_THIS_FILE / "logger_measurement.txt")


def init_logger(filename):
    assert isinstance(filename, pathlib.Path)

    if Dummy.INITIALIZED:
        logger.warning("Logger already initialized")
        return
    Dummy.INITIALIZED = True

    if filename.exists():
        filename.unlink()

    logger.setLevel(logging.DEBUG)
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
