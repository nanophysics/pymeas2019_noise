from pymeas.library_plot_config import PlotConfig


def _func_matplotlib_fig(fig):
    #fig.set_size_inches(3.0, 7.0)
    pass


def _func_matplotlib_ax(ax):
    ax.set_xlim(1e-1, 1e5)
    #ax.set_ylim(1e-9, 1e-5)


def get_plot_config() -> PlotConfig:
    return PlotConfig(
        eseries="E192",
        unit="A",
        func_matplotlib_fig=_func_matplotlib_fig,
        func_matplotlib_ax=_func_matplotlib_ax,
        integral_index_start=10.0,
    )
