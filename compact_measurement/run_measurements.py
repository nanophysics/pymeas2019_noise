from measurement import MeasurementContext, MeasurementController, Speed

CONTEXT = MeasurementContext(
    compact_serial="20000101_01",
    measurement_date="20201130a",
    speed=Speed.MOCKED
)

def main():
    mc = MeasurementController(CONTEXT)
    mc.run_measurements()
    mc.run_qualifikation()
    mc.run_diagrams()

if __name__ == "__main__":
    main()
