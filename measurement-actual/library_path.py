import sys
import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()


def find_append_path():
    dir_measurement = DIRECTORY_OF_THIS_FILE
    for parent in dir_measurement.parents:
        if (parent / "TOPDIR.TXT").exists():
            sys.path.insert(0, str(parent))
            sys.path.insert(0, str(parent / 'src'))
            return dir_measurement
    raise Exception('No file "TOPDIR.TXT" not found in parent directories!')
