import logging
import pathlib
import sys
from importlib import metadata

from ad_low_noise_float_2023 import ad

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

LOGGER_NAME = "logger"
logger = logging.getLogger(LOGGER_NAME)

LOGGING_DEFAULT_FMT = (
    "%(asctime)s - %(name)s - %(threadName)s - %(levelname)7s - %(message)s"
)
LOGGING_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


class Dummy:
    INITIALIZED: bool = False


def init_logger_gui(directory):
    init_logger(
        directory, ("logger_gui.txt", "logger_gui_clone1.txt", "logger_gui_clone2.txt")
    )


def init_logger_condense(directory):
    init_logger(
        directory,
        ("logger_condense.txt", "logger_condense_1.txt", "logger_condense_2.txt"),
    )


def init_logger_composite_plots(directory):
    init_logger(
        directory,
        (
            "logger_composite_plots.txt",
            "logger_composite_plots_1.txt",
            "logger_composite_plots_2.txt",
        ),
    )


def init_logger_measurement(directory):
    assert isinstance(directory, None | pathlib.Path)
    if directory is None:
        directory = pathlib.Path.cwd()
    init_logger(directory, ("logger_measurement.txt",))


def init_logger_append(
    filename, fmt=LOGGING_DEFAULT_FMT, datefmt=LOGGING_DEFAULT_DATEFMT
):
    print(f"logging to {str(filename)}")
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(filename=filename)
    fh.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    logger_ad = logging.getLogger(ad.LOGGER_NAME)
    logger_ad.setLevel(logging.INFO)
    logger_ad.addHandler(ch)
    logger_ad.addHandler(fh)


def init_logger(directory: pathlib.Path, filenames: tuple[str, ...]):
    assert isinstance(directory, pathlib.Path)
    assert isinstance(filenames, list | tuple)

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

    logger.info(f"python={sys.version}")
    try:
        pyside6_version = metadata.version("PySide6")
    except metadata.PackageNotFoundError:
        pyside6_version = "not installed"
    logger.info(f"pyside6={pyside6_version}")
    logger.info(f"cwd={pathlib.Path.cwd()}")
    logger.info(f"sys.argv={sys.argv}")
