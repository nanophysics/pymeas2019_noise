from measurement import MeasurementContext, MeasurementController, Speed

CONTEXT = MeasurementContext(
    compact_serial="20000101_01",
    measurement_date="20210304a",
    speed=Speed.SMOKE,
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
