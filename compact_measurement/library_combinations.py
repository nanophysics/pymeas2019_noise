from enum import Enum
from dataclasses import dataclass

# Compact DA channels
COMPACT_DA_FIRST = 1
COMPACT_DA_LAST = 10

COMPACT_HV_FIRST = 11
COMPACT_HV_LAST = 14

# https://matplotlib.org/2.0.2/examples/color/named_colors.html
COLOR_HV = ("red", "green", "blue", "orange")
COLOR_DA = ("blue", "orange", "black", "green", "red", "cyan", "magenta", "darkgoldenrod", "purple", "lime")  # yellow


class Speed(Enum):
    DETAILED = 1
    SMOKE = 2


# Compact/Supply output voltages
class OutputLevel(Enum):
    MINUS = 0
    ZERO = 1
    PLUS = 2

    @property
    def f_DA_OUT_desired_V(self) -> float:
        return {
            OutputLevel.MINUS: -10.0,
            OutputLevel.ZERO: 0.0,
            OutputLevel.PLUS: +10.0,
        }[self]

    @property
    def compact_da(self) -> str:
        return {
            OutputLevel.MINUS: "-10V",
            OutputLevel.ZERO: "0V",
            OutputLevel.PLUS: "+10V",
        }[self]

    @property
    def compact_hv(self) -> str:
        return {
            OutputLevel.MINUS: "-100V",
            OutputLevel.ZERO: "0V",
            OutputLevel.PLUS: "+100V",
        }[self]

    @property
    def supply(self) -> str:
        return {
            OutputLevel.MINUS: "-14V",
            OutputLevel.PLUS: "+14V",
        }[self]

    @property
    def color_supply(self) -> str:
        return {
            OutputLevel.MINUS: "blue",
            OutputLevel.PLUS: "red",
        }[self]

    def __repr__(self):
        return self.name


# Compcat filter
class FilterBase(Enum):
    pass


class FilterDA(FilterBase):
    DIRECT = 0
    OUT = 1

    def __repr__(self):
        return self.name


class FilterHV(FilterBase):
    OUT_DIR = 2
    OUT_FIL = 3

    def __repr__(self):
        return self.name


# What has to be measured
class MeasurementType(Enum):
    DA = 0
    HV = 1
    SUPPLY = 2

    def __repr__(self):
        return self.name


@dataclass
class Combination:
    measurementtype: MeasurementType
    filter_: FilterBase = None
    level: OutputLevel = None
    channel: int = None  # 1..10
    short: bool = False

    @property
    def channel0(self):
        """
        MeasurementType.DA: channel 0..9 (DA1..DA10)
        MeasurementType.HV: channel 0 (DA1)
        """
        if self.measurementtype == MeasurementType.SUPPLY:
            return 0
        if self.measurementtype == MeasurementType.HV:
            return 0
        if self.short:
            return 0
        assert 1 <= self.channel <= 10
        return self.channel - 1

    @property
    def dirpart_measurementtype(self):
        # DAdirect-10V
        if self.measurementtype == MeasurementType.SUPPLY:
            return f"{self.measurementtype.name}_{self.level.supply}"
        level = self.level.compact_da
        if self.measurementtype == MeasurementType.HV:
            level = self.level.compact_hv
        return f"{self.measurementtype.name}_{self.filter_.name}_{level}"

    @property
    def channel_color_text(self):
        if self.short:
            return "grey-BASENOISE"
        if self.measurementtype == MeasurementType.SUPPLY:
            return f"{self.level.color_supply}-{self.level.supply}"
        if self.measurementtype == MeasurementType.HV:
            color = COLOR_HV[self.channel - COMPACT_HV_FIRST]
            return f"{color}-CH{self.channel:02d}"
        color = COLOR_DA[self.channel - COMPACT_DA_FIRST]
        return f"{color}-DA{self.channel:02d}"

    @property
    def f_DA_OUT_desired_V(self) -> float:
        if self.short:
            return 0.0
        if self.measurementtype == MeasurementType.SUPPLY:
            return 0.0
        return self.level.f_DA_OUT_desired_V

    def configure_pyscan(self, scanner_2020) -> None:
        board_a = scanner_2020.boards[0]
        board_b = scanner_2020.boards[1]

        if self.short:
            # Short
            # Board B, 11
            board_b.set(11)
            return

        if self.measurementtype == MeasurementType.DA:
            # Board A
            # DA.DIRECT: 1-10
            # DA.OUT: 11-20
            if self.filter_ == FilterDA.DIRECT:
                board_a.set(self.channel)
                return
            if self.filter_ == FilterDA.OUT:
                board_a.set(self.channel + 10)
                return
            raise AttributeError()

        if self.measurementtype == MeasurementType.HV:
            # Board B
            # HV.OUT_DIR: 1, 3, 5, 7
            # HV.OUT_FIL: 2, 4, 6, 8
            channel = 1 + (self.channel - COMPACT_HV_FIRST) * 2
            assert 1 <= channel <= 7
            if self.filter_ == FilterHV.OUT_FIL:
                channel += 1
                assert 2 <= channel <= 8
            board_b.set(channel)
            return

        if self.measurementtype == MeasurementType.SUPPLY:
            # Board B
            # SUPPLY 14V: 9
            # SUPPLY -14V: 10
            if self.level == OutputLevel.MINUS:
                board_b.set(9)
                return
            if self.level == OutputLevel.PLUS:
                board_b.set(10)
                return
            raise AttributeError()

        raise AttributeError()

    @property
    def picoscope_input_Vp(self) -> str:
        if self.measurementtype == MeasurementType.DA:
            # return "program_config_instrument_picoscope.InputRange.R_5V" # TODO(peter): Remove
            return "program_config_instrument_picoscope.InputRange.R_100mV"

        if self.measurementtype == MeasurementType.HV:
            # return "program_config_instrument_picoscope.InputRange.R_10V" # TODO(peter): Remove
            return "program_config_instrument_picoscope.InputRange.R_1V"

        if self.measurementtype == MeasurementType.SUPPLY:
            # return "program_config_instrument_picoscope.InputRange.R_5V" # TODO(peter): Remove
            return "program_config_instrument_picoscope.InputRange.R_1V"

        raise AttributeError()


def Combinations(speed):
    # yield Combination(MeasurementType.DA, FilterDA.OUT, OutputLevel.PLUS, short=True)
    # yield Combination(MeasurementType.DA, FilterDA.OUT, OutputLevel.PLUS, COMPACT_DA_FIRST)
    # return
    if speed == Speed.SMOKE:
        yield Combination(MeasurementType.DA, FilterDA.OUT, OutputLevel.PLUS, short=True)
        yield Combination(MeasurementType.DA, FilterDA.OUT, OutputLevel.PLUS, COMPACT_DA_FIRST)
        yield Combination(MeasurementType.DA, FilterDA.OUT, OutputLevel.PLUS, COMPACT_DA_LAST)
        yield Combination(MeasurementType.SUPPLY, level=OutputLevel.PLUS)
        yield Combination(MeasurementType.DA, FilterDA.DIRECT, OutputLevel.ZERO, short=True)
        yield Combination(MeasurementType.HV, FilterHV.OUT_FIL, OutputLevel.MINUS, COMPACT_HV_LAST)
        yield Combination(MeasurementType.HV, FilterHV.OUT_DIR, OutputLevel.ZERO, short=True)
        return

    for level in OutputLevel:
        for filter_ in FilterDA:
            for channel in range(COMPACT_DA_FIRST, COMPACT_DA_LAST + 1):
                yield Combination(MeasurementType.DA, filter_, level, channel)
            yield Combination(MeasurementType.DA, filter_, level, short=True)

    for level in OutputLevel:
        for filter_ in FilterHV:
            for channel in range(COMPACT_HV_FIRST, COMPACT_HV_LAST + 1):
                yield Combination(MeasurementType.HV, filter_, level, channel)
            yield Combination(MeasurementType.HV, filter_, level, short=True)

    for level in (OutputLevel.MINUS, OutputLevel.PLUS):
        yield Combination(MeasurementType.SUPPLY, level=level)


def print_combinations():
    for combination in Combinations(speed=Speed.SMOKE):
        print(combination)


if __name__ == "__main__":
    print_combinations()
