import sys
import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()

TOPDIR = None
DIR_MEASUREMENT = DIRECTORY_OF_THIS_FILE

def find_append_path():
    global TOPDIR  # pylint: disable=global-statement
    for TOPDIR in DIR_MEASUREMENT.parents:
        if (TOPDIR / "TOPDIR.TXT").exists():
            sys.path.insert(0, str(TOPDIR))
            return TOPDIR, DIR_MEASUREMENT
    raise Exception('No file "TOPDIR.TXT" not found in parent directories!')
