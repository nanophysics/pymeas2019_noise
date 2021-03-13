import library_path

TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()

from library_measurement import MeasurementContext, Speed  # pylint: disable=wrong-import-position
from library_controller import MeasurementController  # pylint: disable=wrong-import-position

CONTEXT = MeasurementContext(
    compact_serial="20000101_01",
    measurement_date="20210311a",
    speed=Speed.DETAILED,
    mocked_picoscope=False,
    mocked_scanner=False,
    mocked_compact=False,
    mocked_voltmeter=False
)


def main():
    mc = MeasurementController(CONTEXT)
    mc.run()


if __name__ == "__main__":
    main()
