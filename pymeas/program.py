#
# Make sure that the subrepos are included in the python path
#
import sys
import logging
import pathlib

import library_path

TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()

MSL_EQUIPMENT_PATH = TOPDIR / "libraries" / "msl-equipment"
assert (MSL_EQUIPMENT_PATH / "README.rst").is_file(), f"Subrepo is missing (did you clone with --recursive?): {MSL_EQUIPMENT_PATH}"
sys.path.insert(0, str(MSL_EQUIPMENT_PATH))

MEASUREMENT_ACTUAL = TOPDIR / "measurement-actual"
sys.path.insert(0, str(MEASUREMENT_ACTUAL))

logger = logging.getLogger("logger")

try:
    import numpy as np
except ImportError as ex:
    logger.error(f"ERROR: Failed to import ({ex}). Try: pip install -r requirements.txt")
    sys.exit(0)

# pylint: disable=wrong-import-position
import library_topic
import library_plot
import program_fir_plot

DIRECTORY_TOP = pathlib.Path(__file__).absolute().parent
DIRECTORY_RESULT = "result"


def examine_dir_raw(dir_measurement):
    "Returns the directory with the raw-results"
    assert isinstance(dir_measurement, pathlib.Path)

    dir_arg = None
    if len(sys.argv) > 1:
        dir_arg = sys.argv[1]
        logger.info(f"command line: directory_name={dir_arg}")

    dir_raw = dir_measurement / library_topic.ResultAttributes.result_dir_actual(dir_arg)

    if dir_raw.exists():

        def delete_directory_contents(directory):
            assert isinstance(directory, pathlib.Path)

            for filename in directory.glob("*.*"):
                filename.unlink()

        delete_directory_contents(dir_raw)
    else:
        dir_raw.mkdir(parents=True, exist_ok=True)

    return dir_raw


def reload_if_changed(dir_raw):
    if program_fir_plot.DensityPlot.file_changed(dir_input=dir_raw):
        try:
            list_density = program_fir_plot.DensityPlot.plots_from_directory(dir_input=dir_raw, skip=True)
        except EOFError:
            # File "c:\Projekte\ETH-Fir\pymeas2019_noise\program_fir.py", line 321, in __init__
            # data = pickle.load(f)
            # EOFError: Ran out of input
            return False
        lsd_summary = program_fir_plot.LsdSummary(list_density, directory=dir_raw, trace=False)
        lsd_summary.write_summary_pickle()
        return True
    return False


def iter_dir_raw(dir_measurement):
    for dir_raw in dir_measurement.glob(library_topic.ResultAttributes.RESULT_DIR_PATTERN):
        if not dir_raw.is_dir():
            continue
        yield dir_raw


def run_condense(dir_measurement):
    # if False:
    #   import cProfile
    #   cProfile.run('program.run_condense_0to1()', sort='tottime')
    #   import sys
    #   sys.exit(0)

    # dir_result = dir_measurement / DIRECTORY_RESULT
    # if not dir_result.exists():
    #   dir_result.mkdir()

    for dir_raw in iter_dir_raw(dir_measurement):
        run_condense_dir_raw(dir_raw)


def run_condense_dir_raw(dir_raw, do_plot=True):
    assert isinstance(dir_raw, pathlib.Path)

    run_condense_0to1(dir_raw=dir_raw, do_plot=do_plot, trace=False)
    run_condense_0to1(dir_raw=dir_raw, do_plot=do_plot, trace=True)

    plotData = library_topic.PlotDataSingleDirectory(dir_raw)
    write_presentation_summary_file(plotData, dir_raw)
    if do_plot:
        plotFile = library_plot.PlotFile(plotData=plotData, write_files_directory=dir_raw)
        plotFile.plot_presentations()

    try:
        import library_1_postprocess
    except ModuleNotFoundError:
        logger.error("No library_1_postprocess...")
        return
    logger.info(f"library_1_postprocess.postprocess({dir_raw})")
    library_1_postprocess.postprocess(dir_raw)


def write_presentation_summary_file(plotData, directory):
    assert len(plotData.list_topics) == 1
    dict_result = plotData.list_topics[0].get_as_dict()

    with (directory / "result_presentation.txt").open("w") as f:
        # pprint.PrettyPrinter(indent=2, width=1024, stream=f).pprint(dict_result)
        SpecializedPrettyPrint(stream=f).pprint(dict_result)


def run_condense_0to1(dir_raw, trace=False, do_plot=True):
    assert isinstance(dir_raw, pathlib.Path)

    list_density = program_fir_plot.DensityPlot.plots_from_directory(dir_input=dir_raw, skip=not trace)
    if len(list_density) == 0:
        logger.info(f"SKIPPED: No data for directory {dir_raw}")
        return

    lsd_summary = program_fir_plot.LsdSummary(list_density, directory=dir_raw, trace=trace)
    lsd_summary.write_summary_file(trace=trace)
    if not trace:
        lsd_summary.write_summary_pickle()

    if do_plot:
        file_tag = "_trace" if trace else ""
        lsd_summary.plot(file_tag=file_tag)


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
                if isinstance(i, (list, tuple, np.ndarray)):
                    self._stream.write(key_string + "[")

                    def _repr(v):
                        assert isinstance(v, (float, np.float64, np.float32, np.int32))
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
