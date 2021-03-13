import library_path

library_path.init(__file__)

from library_measurement import MeasurementContext, Speed  # pylint: disable=wrong-import-position
from library_controller import MeasurementController  # pylint: disable=wrong-import-position

DIR_MEASUREMENT = library_path.DIR_MEASUREMENT

CONTEXT = MeasurementContext(
    topdir=library_path.TOPDIR,
    compact_serial="20000101_01",
    measurement_date="20210310a",
    speed=Speed.DETAILED,
    mocked_picoscope=False,
    mocked_scanner=True,
    mocked_compact=True,
    mocked_voltmeter=True
)


def main():
    mc = MeasurementController(CONTEXT)
    mc.run()
    mc.print_duration()


if __name__ == "__main__":
    main()
