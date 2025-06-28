#
# Make sure that the subrepos are included in the python path
#
import logging
import pathlib
import sys

import numpy as np

from . import library_plot, library_topic, program_fir_plot

logger = logging.getLogger("logger")


DIRECTORY_TOP = pathlib.Path(__file__).absolute().parent
DIRECTORY_RESULT = "result"


def examine_dir_raw(dir_measurement):
    "Returns the directory with the raw-results"
    assert isinstance(dir_measurement, pathlib.Path)

    dir_arg = None
    if len(sys.argv) > 1:
        dir_arg = sys.argv[1]
        logger.info(f"command line: directory_name={dir_arg}")

    dir_raw = dir_measurement / library_topic.ResultAttributes.result_dir_actual(
        dir_arg
    )

    create_or_empty_directory(dir_raw)

    return dir_raw


def create_or_empty_directory(dir_raw):
    if dir_raw.exists():

        def delete_directory_contents(directory):
            assert isinstance(directory, pathlib.Path)

            for filename in directory.glob("*.*"):
                filename.unlink()

        delete_directory_contents(dir_raw)
    else:
        dir_raw.mkdir(parents=True, exist_ok=True)


def reload_if_changed(dir_raw, plot_config):
    if program_fir_plot.DensityPlot.file_changed(dir_input=dir_raw):
        try:
            list_density = program_fir_plot.DensityPlot.plots_from_directory(
                dir_input=dir_raw, skip=True
            )
        except EOFError:
            # File "c:\Projekte\ETH-Fir\pymeas2019_noise\program_fir.py", line 321, in __init__
            # data = pickle.load(f)
            # EOFError: Ran out of input
            return False
        lsd_summary = program_fir_plot.LsdSummary(
            plot_config=plot_config,
            list_density=list_density,
            directory=dir_raw,
            trace=False,
        )
        lsd_summary.write_summary_pickle()
        return True
    return False


def iter_dir_raw(dir_measurement):
    for dir_raw in dir_measurement.glob(
        library_topic.ResultAttributes.RESULT_DIR_PATTERN
    ):
        if not dir_raw.is_dir():
            continue
        yield dir_raw


def run_condense(dir_measurement, plot_config, skip_on_error=False):
    # if False:
    #   import cProfile
    #   cProfile.run('program.run_condense_0to1()', sort='tottime')
    #   import sys
    #   sys.exit(0)

    # dir_result = dir_measurement / DIRECTORY_RESULT
    # if not dir_result.exists():
    #   dir_result.mkdir()
    for dir_raw in iter_dir_raw(dir_measurement):
        try:
            run_condense_dir_raw(dir_raw, plot_config=plot_config)
        except library_topic.FrequencyNotFound as e:
            if skip_on_error:
                logger.warning(f"SKIPPED: {e}")
                continue
            raise


def run_condense_dir_raw(dir_raw, plot_config, do_plot=True):
    assert isinstance(dir_raw, pathlib.Path)

    presentations = library_topic.get_presentations(plot_config=plot_config)

    run_condense_0to1(
        dir_raw=dir_raw, plot_config=plot_config, do_plot=do_plot, trace=False
    )
    run_condense_0to1(
        dir_raw=dir_raw, plot_config=plot_config, do_plot=do_plot, trace=True
    )

    plot_data = library_topic.PlotDataSingleDirectory(
        dir_raw=dir_raw, plot_config=plot_config
    )
    write_presentation_summary_file(plot_data, dir_raw)
    if do_plot:
        title = dir_raw.parent.name
        plotFile = library_plot.PlotFile(
            plot_data=plot_data,
            write_files_directory=dir_raw,
            title=title,
            plot_config=plot_config,
            presentations=presentations,
        )

        plotFile.plot_presentations()


def write_presentation_summary_file(plot_data, directory):
    assert len(plot_data.list_topics) == 1
    dict_result = plot_data.list_topics[0].get_as_dict()

    with (directory / "result_presentation.txt").open("w") as f:
        # pprint.PrettyPrinter(indent=2, width=1024, stream=f).pprint(dict_result)
        SpecializedPrettyPrint(stream=f).pprint(dict_result)


def run_condense_0to1(dir_raw, plot_config, trace=False, do_plot=True):
    assert isinstance(dir_raw, pathlib.Path)

    list_density = program_fir_plot.DensityPlot.plots_from_directory(
        dir_input=dir_raw, skip=not trace
    )
    if len(list_density) == 0:
        logger.info(f"SKIPPED: No data for directory {dir_raw}")
        return

    lsd_summary = program_fir_plot.LsdSummary(
        plot_config, list_density, directory=dir_raw, trace=trace
    )
    lsd_summary.write_summary_file(trace=trace)
    if not trace:
        lsd_summary.write_summary_pickle()

    if do_plot:
        file_tag = "_trace" if trace else ""
        title = dir_raw.parent.name
        lsd_summary.plot(file_tag=file_tag, title=title)


class SpecializedPrettyPrint:
    def __init__(self, stream):
        self._stream = stream

    def pprint(self, _dict):
        assert isinstance(_dict, dict)
        self._stream.write("{\n")
        self._print(_dict, "    ")
        self._stream.write("}\n")

    def _print(self, obj, indent):
        if isinstance(obj, dict):
            for k, i in obj.items():
                assert isinstance(k, str)
                key_string = indent + repr(k) + ": "
                if isinstance(i, str):
                    self._stream.write(key_string + repr(i) + ",\n")
                    continue
                if isinstance(i, list | tuple | np.ndarray):
                    self._stream.write(key_string + "[")

                    def _repr(v):
                        assert isinstance(v, float | np.float64 | np.float32 | np.int32)
                        return repr(v)

                    self._stream.write(", ".join([_repr(v) for v in i]))
                    self._stream.write(indent + "],\n")
                    continue
                if isinstance(i, dict):
                    self._stream.write(key_string + "{\n")
                    self._print(i, indent + "    ")
                    self._stream.write(indent + "},\n")
                    continue

                raise Exception(f'Unknown datatype {type(i)} for object "{i}"')
            return
        raise Exception(f'Unknown datatype {type(obj)} for object "{obj}"')
