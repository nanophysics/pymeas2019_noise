import time
import signal
import atexit
import pathlib
import logging

import library_logger

logger = logging.getLogger("logger")

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).absolute().parent

FILENAME_LOCK = DIRECTORY_OF_THIS_FILE / "tmp_filelock_lock.txt"
FILENAME_STATUS = DIRECTORY_OF_THIS_FILE / "tmp_filelock_status.txt"
FILENAME_STOP_HARD = DIRECTORY_OF_THIS_FILE / "tmp_filelock_stop_hard.txt"
FILENAME_STOP_SOFT = DIRECTORY_OF_THIS_FILE / "tmp_filelock_stop_soft.txt"
FILENAME_SKIP_SETTLE = DIRECTORY_OF_THIS_FILE / "tmp_filelock_skip_settle.txt"

REQUEST_CHECKINTERVAL_S = 0.5


class FilelockMeasurement:
    """
    Communication is based on files.
    This class follows the singleton pattern.
    """

    FILE_LOCK = None
    # Some caching of the status of the file
    REQUESTED_STOP = False
    REQUESTED_STOP_HARD = False
    REQUESTED_STOP_SOFT = False
    REQUESTED_SKIP_SETTLE = False
    REQUESTED_STOP_NEXT_S = time.time() + REQUEST_CHECKINTERVAL_S

    def __init__(self):
        if FilelockMeasurement.FILE_LOCK is not None:
            # Singleton-pattern: We may be instantiated multiple times and still refer to the same data
            return

        FilelockMeasurement.FILE_LOCK = FILENAME_LOCK.open("w")

        for filename in (FILENAME_STOP_HARD, FILENAME_STOP_SOFT, FILENAME_SKIP_SETTLE):
            with filename.open("w") as f:
                f.write("Delete this file to stop the measurement")

        FilelockMeasurement.update_status("-")

        def remove_lock():
            assert FilelockMeasurement.FILE_LOCK is not None
            try:
                FilelockMeasurement.FILE_LOCK.close()
            except:  # pylint: disable=bare-except
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
            logger.info(f"{msg} - request hard stop. Next <ctrl-c> will be handled by the operating system")
            # Reset the handler. Next time <ctrl-c> will kill the process by the operating system
            signal.signal(signal.SIGINT, signal.SIG_DFL)

        signal.signal(signal.SIGINT, signal_handler)

    @classmethod
    def cleanup_all_files(cls):
        for filename in (FILENAME_LOCK, FILENAME_STATUS, FILENAME_STOP_SOFT, FILENAME_STOP_HARD, FILENAME_SKIP_SETTLE):
            try:
                filename.unlink()
            except:  # pylint: disable=bare-except
                pass

    @classmethod
    def __check_files(cls):
        assert FilelockMeasurement.FILE_LOCK is not None

        if FilelockMeasurement.REQUESTED_STOP_NEXT_S > time.time():
            return

        FilelockMeasurement.REQUESTED_STOP_NEXT_S = time.time() + REQUEST_CHECKINTERVAL_S

        if not FilelockMeasurement.REQUESTED_STOP_HARD:
            if not FILENAME_STOP_HARD.exists():
                logger.info(f"Stop requested: File '{FILENAME_STOP_HARD.name}' is missing!")
                FilelockMeasurement.REQUESTED_STOP = True
                FilelockMeasurement.REQUESTED_STOP_HARD = True

        if not FilelockMeasurement.REQUESTED_STOP_SOFT:
            if not FILENAME_STOP_SOFT.exists():
                logger.info(f"Stop requested: File '{FILENAME_STOP_SOFT.name}' is missing!")
                FilelockMeasurement.REQUESTED_STOP = True
                FilelockMeasurement.REQUESTED_STOP_SOFT = True

        if not FilelockMeasurement.REQUESTED_SKIP_SETTLE:
            if not FILENAME_SKIP_SETTLE.exists():
                logger.info(f"Stop requested: File '{FILENAME_SKIP_SETTLE.name}' is missing!")
                FilelockMeasurement.REQUESTED_SKIP_SETTLE = True

    @classmethod
    def requested_stop(cls):
        FilelockMeasurement.__check_files()
        if FilelockMeasurement.REQUESTED_STOP:
            logger.info(f"requested_stop() returned True!")
            return True
        return False

    @classmethod
    def requested_stop_soft(cls):
        FilelockMeasurement.__check_files()
        if FilelockMeasurement.REQUESTED_STOP_SOFT:
            logger.info(f"requested_stop_soft() returned True!")
            return True
        return False

    @classmethod
    def requested_stop_hard(cls):
        FilelockMeasurement.__check_files()
        if FilelockMeasurement.REQUESTED_STOP_HARD:
            logger.info(f"requested_stop_hard() returned True!")
            return True
        return False

    @classmethod
    def requested_skip_settle(cls):
        FilelockMeasurement.__check_files()
        if FilelockMeasurement.REQUESTED_SKIP_SETTLE:
            logger.info(f"requested_skip_settle() returned True!")
            return True
        return False

    @classmethod
    def update_status(cls, status: str):
        assert isinstance(status, str)
        logger.info(f"update_status: {status}")
        FILENAME_STATUS.write_text(status)


class FilelockGui:
    @classmethod
    def is_measurement_running(cls):
        assert FilelockMeasurement.FILE_LOCK is None, 'We are the gui. "FilelockMeasurement" must not be initialized!'

        if not FILENAME_LOCK.exists():
            FilelockMeasurement.cleanup_all_files()
            return False
        try:
            FILENAME_LOCK.unlink()
            # The file was not locked anymore
            FilelockMeasurement.cleanup_all_files()
            return False
        except:  # pylint: disable=bare-except
            pass

        return True

    @classmethod
    def stop_measurement_soft(cls):
        assert FilelockMeasurement.FILE_LOCK is None, 'We are the gui. "FilelockMeasurement" must not be initialized!'

        try:
            FILENAME_STOP_SOFT.unlink()
            logger.info(f"successfully removed {FILENAME_STOP_SOFT.name}")
        except:  # pylint: disable=bare-except
            pass

    @classmethod
    def skip_settle(cls):
        assert FilelockMeasurement.FILE_LOCK is None, 'We are the gui. "FilelockMeasurement" must not be initialized!'

        try:
            FILENAME_SKIP_SETTLE.unlink()
            logger.info(f"successfully removed {FILENAME_SKIP_SETTLE.name}")
        except:  # pylint: disable=bare-except
            pass

    @classmethod
    def stop_measurement_hard(cls):
        assert FilelockMeasurement.FILE_LOCK is None, 'We are the gui. "FilelockMeasurement" must not be initialized!'

        try:
            FILENAME_STOP_HARD.unlink()
            logger.info(f"successfully removed {FILENAME_STOP_HARD.name}")
        except:  # pylint: disable=bare-except
            pass

    @classmethod
    def get_status(cls) -> str:
        try:
            return FILENAME_STATUS.read_text()
        except FileNotFoundError:
            return "-"


def main():
    library_logger.init_logger_measurement(DIRECTORY_OF_THIS_FILE)

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
