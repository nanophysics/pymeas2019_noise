import dataclasses
from collections.abc import Callable


@dataclasses.dataclass(frozen=True, repr=True)
class PlotConfig:
    eseries: str = "E12"
    """For example 'E12'"""
    unit: str = "V"
    """For example 'V'"""
    func_matplotlib_ax: Callable | None = None
    """A function with the 'ax' as parameter."""
    func_matplotlib_fig: Callable | None = None
    """A function with the 'fig' as parameter."""
    integral_index_start: float = 0.1
    """[Hz]. Example 0.1"""
