def find_append_path():
    import sys
    import pathlib

    dir_measurement = pathlib.Path(__file__).parent.absolute()
    for parent in dir_measurement.parents:
        if parent.joinpath("TOPDIR.TXT").exists():
            sys.path.insert(0, str(parent))
            return dir_measurement
    raise Exception('No file "TOPDIR.TXT" not found in parent directories!')
