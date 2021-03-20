import library_path

library_path.init(__file__)

from library_measurement import MeasurementContext, Speed  # pylint: disable=wrong-import-position
from library_controller import MeasurementController  # pylint: disable=wrong-import-position

DIR_MEASUREMENT = library_path.DIR_MEASUREMENT

CONTEXT = MeasurementContext(
    topdir=library_path.TOPDIR,
    compact_serial="20000101_01",
    measurement_date="20210319a",
    speed=Speed.DETAILED,
    mocked_picoscope=False,
    mocked_scanner=False,
    mocked_compact=False,
    mocked_voltmeter=False
)


def main():
    mc = MeasurementController(CONTEXT)
    mc.run()
    mc.print_duration()


if __name__ == "__main__":
    main()
