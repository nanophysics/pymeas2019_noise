import library_path

library_path.init(__file__)

from library_controller import (
    MeasurementController,  # pylint: disable=wrong-import-position
)
from library_measurement import (  # pylint: disable=wrong-import-position
    MeasurementContext,
    Speed,
)

DIR_MEASUREMENT = library_path.DIR_MEASUREMENT

CONTEXT = MeasurementContext(
    topdir=library_path.TOPDIR,
    compact_serial="20200918_75",
    measurement_date="20210614a",
    #speed=Speed.DETAILED_NO_HV_AMP, # no HV amp assembled
    speed=Speed.DETAILED_WITH_HV_AMP,
    mocked_picoscope=False,
    mocked_scanner=False,
    mocked_compact=False,
    mocked_voltmeter=False,
    mocked_hv_amp=True
)


def main():
    mc = MeasurementController(CONTEXT)
    mc.run()
    mc.print_duration()


if __name__ == "__main__":
    main()
