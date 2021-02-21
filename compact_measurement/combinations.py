from enum import Enum
from dataclasses import dataclass

# Compact DA channels
COMPACT_DA_FIRST = 1
COMPACT_DA_LAST = 10

COMPACT_HV_FIRST = 11
COMPACT_HV_LAST = 14

COLOR_SUPPLY = 'red'
COLOR_HV = ('red', 'green', 'blue', 'orange')
COLOR_DA = ('red', 'green', 'blue', 'orange', 'red', 'green', 'blue', 'orange', 'red', 'green')

# Compact/Supply output voltages
class OutputLevel(Enum):
    MINUS = 0
    ZERO = 1
    PLUS = 2

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

    def __repr__(self):
        return self.name


# Compcat filter
class Filter(Enum):
    DIRECT = 0
    OUT = 1

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
    filter_: Filter = None
    level: OutputLevel = None
    channel: int = None
    short: bool = False

    @property
    def dirpart(self):
        # DAdirect-10V/DA01
        if self.measurementtype == MeasurementType.SUPPLY:
            return f"{self.measurementtype.name}_{self.level.supply}"
        level = self.level.compact_da
        if self.measurementtype == MeasurementType.HV:
            level = self.level.compact_hv
        return f"{self.filter_.name}_{level}_{self.measurementtype.name}"

    @property
    def channel_text(self):
        if self.short:
            return 'grey-BASENOISE'
        if self.measurementtype == MeasurementType.SUPPLY:
            return f'{COLOR_SUPPLY}-SUPPLY'
        if self.measurementtype == MeasurementType.HV:
            color = COLOR_HV[self.channel-COMPACT_HV_FIRST]
            return f"{color}-CH{self.channel:02d}"
        color = COLOR_DA[self.channel-COMPACT_DA_FIRST]
        return f"{color}-DA{self.channel:02d}"

def combinations(smoketest=False):
    if smoketest:
        yield Combination(MeasurementType.DA, Filter.OUT, OutputLevel.PLUS, COMPACT_DA_FIRST)
        yield Combination(MeasurementType.DA, Filter.OUT, OutputLevel.ZERO, short=True)
        yield Combination(MeasurementType.HV, Filter.DIRECT, OutputLevel.MINUS, COMPACT_DA_LAST)
        yield Combination(MeasurementType.HV, Filter.DIRECT, OutputLevel.ZERO, short=True)
        yield Combination(MeasurementType.SUPPLY, level=OutputLevel.PLUS)
        return

    for level in OutputLevel:
        for filter_ in Filter:
            for channel in range(COMPACT_DA_FIRST, COMPACT_DA_LAST + 1):
                yield Combination(MeasurementType.DA, filter_, level, channel)
            yield Combination(MeasurementType.DA, filter_, level, short=True)

    for level in OutputLevel:
        for filter_ in Filter:
            for channel in range(COMPACT_HV_FIRST, COMPACT_HV_LAST + 1):
                yield Combination(MeasurementType.HV, filter_, level, channel)
            yield Combination(MeasurementType.HV, filter_, level, short=True)

    for level in (OutputLevel.MINUS, OutputLevel.PLUS):
        yield Combination(MeasurementType.SUPPLY, level=level)

def print_combinations():
    for combination in combinations():
        print(combination)


if __name__ == "__main__":
    print_combinations()
