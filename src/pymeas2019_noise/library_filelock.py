import atexit
import enum
import io
import logging
import os
import pathlib
import signal
import time
from enum import Enum

from . import library_logger

logger = logging.getLogger("logger")


FILENAME_CONFIG_MEASUREMENTS = "config_measurement.py"


def find_topdir() -> pathlib.Path:
    cwd = pathlib.Path.cwd()
    config_measurement = cwd / FILENAME_CONFIG_MEASUREMENTS
    assert config_measurement.is_file(), str(config_measurement)
    return cwd


class ExitCode(Enum):
    OK = 0
    ERROR_INPUT_NOT_SETTLE = 40
    ERROR_PICOSCOPE = 41
    ERROR_QUEUE_FULL = 42
    ERROR = 43
    CTRL_C = 44

    def os_exit(self, msg=None):
        os_exit(self, msg=msg)


def os_exit(exit_code: ExitCode, msg=None):
    assert isinstance(exit_code, ExitCode)
    text = f"Exit with {exit_code.name}({exit_code.value}): {msg}"
    if msg is None:
        text = f"Exit with {exit_code.name}({exit_code.value})"
    if exit_code == ExitCode.OK:
        logger.info(text)
    else:
        logger.error(text)
    os._exit(exit_code.value)


class LockTag(enum.StrEnum):
    FILENAME_LOCK = "tmp_filelock_lock.txt"
    FILENAME_STATUS = "tmp_filelock_status.txt"
    FILENAME_STOP_HARD = "tmp_filelock_stop_hard.txt"
    FILENAME_STOP_SOFT = "tmp_filelock_stop_soft.txt"
    FILENAME_SKIP_SETTLE = "tmp_filelock_skip_settle.txt"

    @property
    def filename(self) -> pathlib.Path:
        topdir = find_topdir()
        return topdir / self.value

    def open(self, mode: str) -> io.TextIOWrapper:
        return self.filename.open(mode)

    def write_text(self, data: str) -> int:
        return self.filename.write_text(data=data)

    def read_text(self) -> str:
        return self.filename.read_text()

    def exists(self) -> bool:
        return self.filename.exists()

    def unlink(self, missing_ok=False) -> None:
        return self.filename.unlink(missing_ok=missing_ok)


REQUEST_CHECKINTERVAL_S = 0.5


class FilelockMeasurement:
    """
    Communication is based on files.
    This class follows the singleton pattern.
    """

    FILE_LOCK: io.TextIOWrapper | None = None
    # Some caching of the status of the file
    REQUESTED_STOP = False
    REQUESTED_STOP_HARD: bool = False
    REQUESTED_STOP_SOFT: bool = False
    REQUESTED_SKIP_SETTLE: bool = False
    REQUESTED_STOP_NEXT_S: float = time.time() + REQUEST_CHECKINTERVAL_S

    def __init__(self) -> None:
        if FilelockMeasurement.FILE_LOCK is not None:
            # Singleton-pattern: We may be instantiated multiple times and still refer to the same data
            return

        FilelockMeasurement.FILE_LOCK = LockTag.FILENAME_LOCK.filename.open("w")

        for locktag in (
            LockTag.FILENAME_STOP_HARD,
            LockTag.FILENAME_STOP_SOFT,
            LockTag.FILENAME_SKIP_SETTLE,
        ):
            with locktag.open("w") as f:
                f.write("Delete this file to stop the measurement")

        FilelockMeasurement.update_status("-")

        def remove_lock():
            assert FilelockMeasurement.FILE_LOCK is not None
            try:
                FilelockMeasurement.FILE_LOCK.close()
            except:  # pylint: disable=bare-except  # noqa: E722
                pass
            FilelockMeasurement.cleanup_all_files()

        atexit.register(remove_lock)

        def signal_handler(sig, frame):  # pylint: disable=unused-argument
            msg = "You pressed Ctrl+C!"
            if not FilelockMeasurement.REQUESTED_STOP_SOFT:
                # First time: Request a soft stop
                FilelockMeasurement.REQUESTED_STOP_SOFT = True
                logger.info(f"{msg} - request soft stop.")
                return
            # Second time: Request a hard stop
            FilelockMeasurement.REQUESTED_STOP_HARD = True
            logger.info(
                f"{msg} - request hard stop. Next <ctrl-c> will be handled by the operating system"
            )
            # Reset the handler. Next time <ctrl-c> will kill the process by the operating system
            signal.signal(signal.SIGINT, signal.SIG_DFL)

        signal.signal(signal.SIGINT, signal_handler)

    @classmethod
    def cleanup_all_files(cls):
        for filename in (
            LockTag.FILENAME_LOCK,
            LockTag.FILENAME_STATUS,
            LockTag.FILENAME_STOP_SOFT,
            LockTag.FILENAME_STOP_HARD,
            LockTag.FILENAME_SKIP_SETTLE,
        ):
            try:
                filename.unlink()
            except:  # pylint: disable=bare-except  # noqa: E722
                pass

    @classmethod
    def __check_files(cls):
        assert FilelockMeasurement.FILE_LOCK is not None

        if FilelockMeasurement.REQUESTED_STOP_NEXT_S > time.time():
            return

        FilelockMeasurement.REQUESTED_STOP_NEXT_S = (
            time.time() + REQUEST_CHECKINTERVAL_S
        )

        if not FilelockMeasurement.REQUESTED_STOP_HARD:
            if not LockTag.FILENAME_STOP_HARD.exists():
                logger.info(
                    f"Stop requested: File '{LockTag.FILENAME_STOP_HARD}' is missing!"
                )
                FilelockMeasurement.REQUESTED_STOP = True
                FilelockMeasurement.REQUESTED_STOP_HARD = True

        if not FilelockMeasurement.REQUESTED_STOP_SOFT:
            if not LockTag.FILENAME_STOP_SOFT.exists():
                logger.info(
                    f"Stop requested: File '{LockTag.FILENAME_STOP_SOFT}' is missing!"
                )
                FilelockMeasurement.REQUESTED_STOP = True
                FilelockMeasurement.REQUESTED_STOP_SOFT = True

        if not FilelockMeasurement.REQUESTED_SKIP_SETTLE:
            if not LockTag.FILENAME_SKIP_SETTLE.exists():
                logger.info(
                    f"Stop requested: File '{LockTag.FILENAME_SKIP_SETTLE}' is missing!"
                )
                FilelockMeasurement.REQUESTED_SKIP_SETTLE = True

    @classmethod
    def requested_stop(cls):
        FilelockMeasurement.__check_files()
        if FilelockMeasurement.REQUESTED_STOP:
            logger.info("requested_stop() returned True!")
            return True
        return False

    @classmethod
    def requested_stop_soft(cls):
        FilelockMeasurement.__check_files()
        if FilelockMeasurement.REQUESTED_STOP_SOFT:
            logger.info("requested_stop_soft() returned True!")
            return True
        return False

    @classmethod
    def requested_stop_hard(cls):
        FilelockMeasurement.__check_files()
        if FilelockMeasurement.REQUESTED_STOP_HARD:
            logger.info("requested_stop_hard() returned True!")
            return True
        return False

    @classmethod
    def requested_skip_settle(cls):
        FilelockMeasurement.__check_files()
        if FilelockMeasurement.REQUESTED_SKIP_SETTLE:
            logger.info("requested_skip_settle() returned True!")
            return True
        return False

    @classmethod
    def update_status(cls, status: str):
        assert isinstance(status, str)
        logger.info(f"update_status: {status}")
        LockTag.FILENAME_STATUS.write_text(status)


class FilelockGui:
    @classmethod
    def is_measurement_running(cls):
        assert FilelockMeasurement.FILE_LOCK is None, (
            'We are the gui. "FilelockMeasurement" must not be initialized!'
        )

        if not LockTag.FILENAME_LOCK.exists():
            FilelockMeasurement.cleanup_all_files()
            return False
        try:
            LockTag.FILENAME_LOCK.unlink()
            # The file was not locked anymore
            FilelockMeasurement.cleanup_all_files()
            return False
        except:  # pylint: disable=bare-except  # noqa: E722
            pass

        return True

    @classmethod
    def stop_measurement_soft(cls):
        assert FilelockMeasurement.FILE_LOCK is None, (
            'We are the gui. "FilelockMeasurement" must not be initialized!'
        )

        try:
            LockTag.FILENAME_STOP_SOFT.unlink()
            logger.info(f"successfully removed '{LockTag.FILENAME_STOP_SOFT}'")
        except:  # pylint: disable=bare-except  # noqa: E722
            pass

    @classmethod
    def skip_settle(cls):
        assert FilelockMeasurement.FILE_LOCK is None, (
            'We are the gui. "FilelockMeasurement" must not be initialized!'
        )

        try:
            LockTag.FILENAME_SKIP_SETTLE.unlink()
            logger.info(f"successfully removed '{LockTag.FILENAME_SKIP_SETTLE}'")
        except:  # pylint: disable=bare-except  # noqa: E722
            pass

    @classmethod
    def stop_measurement_hard(cls):
        assert FilelockMeasurement.FILE_LOCK is None, (
            'We are the gui. "FilelockMeasurement" must not be initialized!'
        )

        try:
            LockTag.FILENAME_STOP_HARD.unlink()
            logger.info(f"successfully removed '{LockTag.FILENAME_STOP_HARD}'")
        except:  # pylint: disable=bare-except  # noqa: E722
            pass

    @classmethod
    def get_status(cls) -> str:
        try:
            return LockTag.FILENAME_STATUS.read_text()
        except FileNotFoundError:
            return "-"


def main():
    directory = pathlib.Path.cwd()
    library_logger.init_logger_measurement(directory=directory)

    filelock = FilelockMeasurement()
    for i in range(1000):
        if i == 2:
            FilelockGui.stop_measurement_soft()
        if i == 5:
            FilelockGui.stop_measurement_hard()
        logger.info(f"sleep {i}")
        time.sleep(1)
        if filelock.requested_stop_hard():
            return


if __name__ == "__main__":
    main()
