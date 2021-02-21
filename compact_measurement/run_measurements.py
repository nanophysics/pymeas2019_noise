import pathlib
import combinations
from measurement import Measurement, MeasurementContext

import library_path

TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()

CONTEXT = MeasurementContext(
    topdir=TOPDIR,
    compact_serial="20000101_01",
    measurement_date="20201130a",
    compact_pythonpath=pathlib.Path("C:/Projekte/ETH-Compact/git_compact_2012/Drivers/compact_2012"),
    scanner_pythonpath=pathlib.Path("C:/Projekte/ETH-scanner_pyb/software")
)

def run_measurements():
    for combination in combinations.combinations(smoketest=False):
        # print(combination)
        with Measurement(CONTEXT, combination) as measurement:
            measurement.connect_pyboards()
            measurement.create_directory()
            measurement.configure_compact()
            measurement.configure_pyscan()
            measurement.measure()
            measurement.commit()

def run_qualifikation():
    pass

def run_diagrams():
    pass

if __name__ == "__main__":
    run_measurements()
    run_qualifikation()
    run_diagrams()
