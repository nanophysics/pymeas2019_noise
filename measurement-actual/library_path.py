import hashlib
import importlib
import os
import pathlib
import sys

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent.absolute()

TOPDIR = None
DIR_MEASUREMENT = None
PATH_SHA256 = None

MSL_EQUIPMENT_PATH = None


def clean_path(topdir):
    for entry in sys.path.copy():

        def remove_unneeded_entry(entry):
            entry_pathlib = pathlib.Path(entry).absolute()
            if not entry_pathlib.exists():
                sys.path.remove(entry)
                return
            if entry_pathlib.name == "measurement-actual":
                # This entry was added by ${workspaceFolder}/project.pythonenv
                # Remove it to add it again but as 'DIR_MEASUREMENT'
                sys.path.remove(entry)
                return
            if entry_pathlib in (DIR_MEASUREMENT, topdir):
                sys.path.remove(entry)

        remove_unneeded_entry(entry)

    sys.path.insert(0, str(topdir))
    sys.path.insert(0, str(DIR_MEASUREMENT))
    # print('**** PATH=' + ';'.join(sys.path))


def find_topdir():
    for topdir in DIR_MEASUREMENT.parents:
        if (topdir / "TOPDIR.TXT").exists():
            return topdir
    raise Exception('No file "TOPDIR.TXT" not found in parent directories!')


def path_sha256():
    m = hashlib.sha256()
    path = ";".join(sys.path)
    m.update(path.encode("utf-8"))
    return m.hexdigest()


def add_msl_equipment():
    global MSL_EQUIPMENT_PATH  # pylint: disable=global-statement
    MSL_EQUIPMENT_PATH = TOPDIR / "libraries" / "msl-equipment"
    assert (MSL_EQUIPMENT_PATH / "README.rst").is_file(), f"Subrepo is missing (did you clone with --recursive?): {MSL_EQUIPMENT_PATH}"
    sys.path.insert(0, str(MSL_EQUIPMENT_PATH))


def init(startfile):
    global TOPDIR  # pylint: disable=global-statement
    global DIR_MEASUREMENT  # pylint: disable=global-statement
    global PATH_SHA256  # pylint: disable=global-statement
    if TOPDIR is not None:
        if PATH_SHA256 != path_sha256():
            print("WARNING: TOPDIR is already defined and path changed: sys.path=" + ";".join(sys.path))
        return
    DIR_MEASUREMENT = pathlib.Path(startfile).absolute().parent
    os.chdir(str(DIR_MEASUREMENT))
    TOPDIR = find_topdir()
    clean_path(TOPDIR)
    add_msl_equipment()
    importlib.invalidate_caches()
    PATH_SHA256 = path_sha256()
