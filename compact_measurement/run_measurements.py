from library_measurement import MeasurementContext, Speed
from library_measurement_controller import MeasurementController

CONTEXT = MeasurementContext(
    compact_serial="20000101_01",
    measurement_date="20210306a",
    speed=Speed.DETAILED,
    mocked_picoscope=False,
    mocked_scanner=True,
    mocked_compact=True
)

def main():
    mc = MeasurementController(CONTEXT)
    mc.run_measurements()
    mc.run_qualifikation()
    mc.run_diagrams()

if __name__ == "__main__":
    main()
