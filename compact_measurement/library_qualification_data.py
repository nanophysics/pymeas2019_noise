import math
import logging
from dataclasses import dataclass

logger = logging.getLogger("logger")

@dataclass
class Line:
    measurement_date: str
    measurement_type: str
    channel: int
    unit: str
    min: float
    max: float
    measured: float

    @staticmethod
    def writeheader(f):
        f.write(
            "\t".join(
                (
                    "Serial-Date",
                    "Type",
                    "Channel",
                    "Unit",
                    "min",
                    "max",
                    "measured",
                    "percent",
                    "abs(percent)",
                )
            )
        )
        f.write("\n")

    def writeline(self, f):
        f.write(
            "\t".join(
                (
                    self.measurement_date,
                    self.measurement_type,
                    self.channel2,
                    self.unit,
                    f"{self.min:0.6f}",
                    f"{self.max:0.6f}",
                    f"{self.measured:0.6f}",
                    f"{self.error_relative:0.6f}",
                    f"{self.error_relative_abs:0.6f}",
                )
            )
        )
        f.write("\n")

    @property
    def channel2(self) -> float:
        if self.channel is None:
            return "-"
        return str(self.channel)

    @property
    def error_relative(self) -> str:
        diff = self.measured - (self.min + self.max) / 2.0
        return diff / (self.max - self.min)

    @property
    def error_relative_abs(self) -> str:
        return math.fabs(self.error_relative)
