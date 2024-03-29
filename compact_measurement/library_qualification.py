# The user can use a postprocess to evaluate the quality of a device for example.
# Just delete this file if no need for postprocess
# The example shows the calculation of flicker noise 0.1 ... 10 Hz
# The measurement time could be set to 60s for example.
# Just start run_0_measure.bat and observe the result

from enum import Enum
import pathlib
import logging

from library_qualification_data import Line
from library_measurement import Measurement
import library_combinations
from pymeas.library_topic import Topic, get_presentations
from pymeas.library_plot_config import PlotConfig
from compact_measurement.pyspreadsheet import ExcelReader, Row

logger = logging.getLogger("logger")


class Bool(Enum):
    TRUE = True
    FALSE = False


class Filter(Enum):
    FilterDA_DIRECT = library_combinations.FilterDA.DIRECT.value  # pylint: disable=no-member
    FilterDA_OUT = library_combinations.FilterDA.OUT.value  # pylint: disable=no-member
    FilterHV_OUT_DIR = library_combinations.FilterHV.OUT_DIR.value  # pylint: disable=no-member
    FilterHV_OUT_FIL = library_combinations.FilterHV.OUT_FIL.value  # pylint: disable=no-member


class Qualification:
    def __init__(self, dir_measurement_date: pathlib.Path):
        assert isinstance(dir_measurement_date, pathlib.Path)
        self.dir_measurement_date = dir_measurement_date
        self.list_results = []

        self._plot_config_dummy = PlotConfig(
            eseries="E12",
            unit="V",
            integral_index_start=0.1,
        )
        self._presentations = get_presentations(plot_config=self._plot_config_dummy)

        excel_file = pathlib.Path(__file__).absolute().parent / "library_qualification_tolerances.xlsx"

        excel = ExcelReader(excel_file)
        self.qualification_rows = excel.tables.Qualification.rows

    def _iter_enum(self, cell, enum_class):
        if cell.text == "":
            yield from enum_class
            return

        if enum_class == library_combinations.OutputLevel:
            if cell.text == "MINUS/PLUS":
                yield library_combinations.OutputLevel.MINUS
                yield library_combinations.OutputLevel.PLUS
                return

        yield cell.asenum(enum_class)

    def _iter_rows(self, combination):
        assert isinstance(combination, library_combinations.Combination)

        def eq(a, b):
            assert type(a) is type(b)
            return a == b

        for row in self.qualification_rows:  # pylint: disable=too-many-nested-blocks
            short = row.cols.Short.asenum(Bool)
            if eq(short.value, combination.short):
                for measurementtype in self._iter_enum(row.cols.MeasurementType, library_combinations.MeasurementType):
                    if eq(measurementtype, combination.measurementtype):
                        for level in self._iter_enum(row.cols.OutputLevel, library_combinations.OutputLevel):
                            if eq(level, combination.level):
                                if combination.filter_ is None:
                                    yield row
                                    continue
                                for filter_ in self._iter_enum(row.cols.Filter, Filter):
                                    if eq(filter_.value, combination.filter_.value):
                                        yield row

    def qualify_using_calc(self, measurement):
        assert isinstance(measurement, Measurement)

        for row in self._iter_rows(measurement.combination):
            functionname = row.cols.PythonFunction.text
            f = getattr(self, functionname)
            f(row, measurement)

    def write_qualification(self):
        file_qualification = self.dir_measurement_date / "result_qualification.csv"
        with file_qualification.open("w") as f:
            Line.writeheader(f)
            # TODO: Move to data class
            self.list_results.sort(key=lambda m: (m.measurement_date, m.measurement_type, m.pythonfunction, m.channel2))
            for result in self.list_results:
                result.writeline(f)

    def _append(self, row, measurement, measured, comment=""):
        assert isinstance(row, Row)
        assert isinstance(measurement, Measurement)
        assert isinstance(measured, float)
        assert isinstance(comment, str)
        self.list_results.append(
            Line(
                measurement_date=self.dir_measurement_date.name,
                measurement_type=measurement.combination.dirpart_measurementtype,
                pythonfunction=row.cols.PythonFunction.text,
                channel=measurement.combination.channel,
                unit=row.cols.Unit.text,
                min=row.cols.limit_min.float,
                max=row.cols.limit_max.float,
                measured=measured,
                comment=comment,
            )
        )

    def qual_voltage(self, row, measurement):
        assert isinstance(row, Row)
        assert isinstance(measurement, Measurement)
        measured_V = measurement.measurement_channel_voltage.read()
        if measured_V is None:
            logger.warning(f"{measurement.combination}: NO VOLTAGE")
            return
        logger.debug(f"{measurement.combination}: Voltage {measured_V}")
        self._append(row, measurement, measured=measured_V)

    def qual_band_LSD(self, row, measurement):
        assert isinstance(row, Row)
        assert isinstance(measurement, Measurement)
        range_lower = row.cols.lower.float
        range_upper = row.cols.upper.float
        comment = f"{range_lower}<x<{range_upper} {row.cols.UnitRange.text}"

        subtract_basenoise = measurement.combination.channel is not None
        topic = self._read_topic(measurement=measurement, subtract_basenoise=subtract_basenoise)
        LSD = self._presentations.dict["LSD"].get_as_dict(topic)

        MIN = -1000.0
        max_value = MIN
        for x, y in zip(LSD["x"], LSD["y"]):
            x = float(x)
            y = float(y)
            if range_lower < x < range_upper:
                max_value = max(y, max_value)

        if max_value < -1.0:
            logger.error(f"No measurements found in range {comment}")
            return

        self._append(row, measurement, measured=max_value, comment=comment)

    def _read_topic(self, measurement, subtract_basenoise=True):
        assert isinstance(measurement, Measurement)

        dir_raw = measurement.dir_measurement_channel
        topic = Topic.load(dir_raw=dir_raw, plot_config=self._plot_config_dummy, presentations=self._presentations)

        # basenoise
        if subtract_basenoise:
            dir_raw_basenoise = dir_raw.parent / "raw-grey-BASENOISE"
            if dir_raw_basenoise.exists():
                topic_basenoise = Topic.load(dir_raw=dir_raw_basenoise, plot_config=self._plot_config_dummy, presentations=self._presentations)
                topic.set_basenoise(topic_basenoise)

        return topic

    def qual_flickernoise(self, row, measurement):
        assert isinstance(row, Row)
        assert isinstance(measurement, Measurement)

        topic = self._read_topic(measurement)

        _flickernoise_Vrms, flickernoise_minus_basenoise_Vrms, comment = topic.flickernoise()

        if measurement.combination.short:  # short: BASENOISE is measured. Do not substract basenoise
            flickernoise = _flickernoise_Vrms
        else:
            flickernoise = flickernoise_minus_basenoise_Vrms

        self._append(row, measurement, measured=flickernoise, comment=comment)

    def qual_step_size(self, row, measurement):
        assert isinstance(row, Row)
        assert isinstance(measurement, Measurement)

        topic = self._read_topic(measurement)
        stepsize = self._presentations.dict["STEPSIZE"].get_as_dict(topic)

        range_lower = row.cols.lower.float
        comment = f"range_lower={range_lower} {row.cols.UnitRange.text}"

        _sum = 0.0
        for x, y in zip(stepsize["x"], stepsize["y"]):
            x = float(x)
            y = float(y)
            if x < range_lower:
                continue
            _sum += y

        self._append(row, measurement, measured=_sum, comment=comment)
