#
# Make sure that the subrepos are included in the python path
#
import sys
import signal
import logging
import pathlib

TOPDIR = pathlib.Path(__file__).parent.absolute()
MSL_EQUIPMENT_PATH = TOPDIR / "libraries" / "msl-equipment"
assert (MSL_EQUIPMENT_PATH / "README.rst").is_file(), f"Subrepo is missing (did you clone with --recursive?): {MSL_EQUIPMENT_PATH}"
sys.path.insert(0, str(MSL_EQUIPMENT_PATH))

MEASUREMENT_ACTUAL = "measurement-actual"
sys.path.insert(0, str(TOPDIR / MEASUREMENT_ACTUAL))

try:
    import numpy as np
except ImportError as ex:
    print(f"ERROR: Failed to import ({ex}). Try: pip install -r requirements.txt")
    sys.exit(0)

import library_topic  # pylint: disable=wrong-import-position
import library_plot  # pylint: disable=wrong-import-position
import program_fir  # pylint: disable=wrong-import-position

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

DIRECTORY_TOP = pathlib.Path(__file__).absolute().parent
DIRECTORY_RESULT = "result"

DEFINED_BY_SETUP = "DEFINED_BY_SETUP"


class ConfigStep:  # pylint: disable=too-many-instance-attributes
    def __init__(self, dict_values={}):  # pylint: disable=dangerous-default-value
        self.stepname = DEFINED_BY_SETUP
        self.fir_count = DEFINED_BY_SETUP
        self.fir_count_skipped = DEFINED_BY_SETUP
        self.input_Vp = DEFINED_BY_SETUP
        self.skalierungsfaktor = DEFINED_BY_SETUP
        self.input_channel = DEFINED_BY_SETUP
        self.duration_s = DEFINED_BY_SETUP
        self.diagram_legend = DEFINED_BY_SETUP
        self.result_gain = DEFINED_BY_SETUP
        self.result_unit = DEFINED_BY_SETUP
        self.reference = DEFINED_BY_SETUP
        self.bandwitdth = DEFINED_BY_SETUP
        self.offset = DEFINED_BY_SETUP
        self.resolution = DEFINED_BY_SETUP
        self.dt_s = DEFINED_BY_SETUP

        self.update_by_dict(dict_values)

    def _update_element(self, key, value):
        assert key in self.__dict__
        self.__dict__[key] = value

    def update_by_dict(self, dict_config_setup):
        for key, value in dict_config_setup.items():
            self._update_element(key, value)


class HandlerCtrlC:
    def __init__(self):
        self.__ctrl_c_pressed = False
        signal.signal(signal.SIGINT, self.__signal_handler)

    def __signal_handler(self, sig, frame):  # pylint: disable=unused-argument
        print("You pressed Ctrl+C!")
        self.__ctrl_c_pressed = True

    @property
    def ctrl_c_pressed(self):
        if self.__ctrl_c_pressed:
            # Reset the handler
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        return self.__ctrl_c_pressed


handlerCtrlC = HandlerCtrlC()


class ConfigSetup:
    def __init__(self):
        self.diagram_legend = DEFINED_BY_SETUP
        self.setup_name = DEFINED_BY_SETUP
        self.module_instrument = DEFINED_BY_SETUP
        self.steps = DEFINED_BY_SETUP

    # def get_filename_data(self, extension, directory=DIRECTORY_0_RAW):
    #   filename = f'data_{self.setup_name}'
    #   return os.path.join(directory, f'{filename}.{extension}')

    # def create_directories(self):
    #   for directory in (DIRECTORY_0_RAW, DIRECTORY_1_CONDENSED, DIRECTORY_2_RESULT):
    #       if not os.path.exists(directory):
    #         os.makedirs(directory)

    def delete_directory_contents(self, directory):
        assert isinstance(directory, pathlib.Path)

        for filename in directory.glob("*.*"):
            filename.unlink()

    def _update_element(self, key, value):
        assert key in self.__dict__
        if key == "steps":
            self.__dict__[key] = [ConfigStep(v) for v in value]
            return
        self.__dict__[key] = value

    def update_by_dict(self, dict_config_setup):
        for key, value in dict_config_setup.items():
            self._update_element(key, value)

    def update_by_channel_file(self, dict_config_setup):
        self.update_by_dict(dict_config_setup)

    def measure_for_all_steps(self, dir_measurement, directory_name=None):
        assert isinstance(dir_measurement, pathlib.Path)
        assert isinstance(directory_name, (type(None), str))

        dir_raw = dir_measurement / library_topic.ResultAttributes.result_dir_actual(directory_name)
        if dir_raw.exists():
            self.delete_directory_contents(dir_raw)
        else:
            dir_raw.mkdir(parents=True, exist_ok=True)

        for configStep in self.steps:
            picoscope = self.module_instrument.Instrument(configStep)  # pylint: disable=no-member
            picoscope.connect()
            sample_process = program_fir.SampleProcess(program_fir.SampleProcessConfig(configStep), dir_raw)
            picoscope.acquire(configStep=configStep, stream_output=sample_process.output, handlerCtrlC=handlerCtrlC)
            picoscope.close()

            if handlerCtrlC.ctrl_c_pressed:
                break

        return dir_raw


def get_configSetup_by_filename(dict_config_setup):
    import config_common

    config = ConfigSetup()
    config.update_by_dict(config_common.DICT_CONFIG_SETUP_DEFAULTS)
    config.update_by_channel_file(dict_config_setup)
    return config


def reload_if_changed(dir_raw):
    if program_fir.DensityPlot.file_changed(dir_input=dir_raw):
        try:
            list_density = program_fir.DensityPlot.plots_from_directory(dir_input=dir_raw, skip=True)
        except EOFError:
            # File "c:\Projekte\ETH-Fir\pymeas2019_noise\program_fir.py", line 321, in __init__
            # data = pickle.load(f)
            # EOFError: Ran out of input
            return False
        lsd_summary = program_fir.LsdSummary(list_density, directory=dir_raw, trace=False)
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
    run_condense_0to1(dir_raw=dir_raw, do_plot=do_plot, trace=False)
    run_condense_0to1(dir_raw=dir_raw, do_plot=do_plot, trace=True)

    plotData = library_topic.PlotDataSingleDirectory(dir_raw)
    write_presentation_summary_file(plotData, dir_raw)
    if do_plot:
        library_plot.do_plots(plotData=plotData, do_show=False, write_files=("png",), write_files_directory=dir_raw)

    try:
        import library_1_postprocess
    except ModuleNotFoundError:
        print("No library_1_postprocess...")
        return
    print(f"library_1_postprocess.postprocess({dir_raw})")
    library_1_postprocess.postprocess(dir_raw)


def write_presentation_summary_file(plotData, directory):
    assert len(plotData.listTopics) == 1
    dict_result = plotData.listTopics[0].get_as_dict()

    with (directory / "result_presentation.txt").open("w") as f:
        # pprint.PrettyPrinter(indent=2, width=1024, stream=f).pprint(dict_result)
        SpecializedPrettyPrint(stream=f).pprint(dict_result)


def run_condense_0to1(dir_raw, trace=False, do_plot=True):
    list_density = program_fir.DensityPlot.plots_from_directory(dir_input=dir_raw, skip=not trace)
    if len(list_density) == 0:
        print(f"SKIPPED: No data for directory {dir_raw}")
        return

    lsd_summary = program_fir.LsdSummary(list_density, directory=dir_raw, trace=trace)
    lsd_summary.write_summary_file(trace=trace)
    if not trace:
        lsd_summary.write_summary_pickle()

    if do_plot:
        file_tag = "_trace" if trace else ""
        lsd_summary.plot(file_tag=file_tag)


def measure(configSetup, dir_measurement):
    assert isinstance(dir_measurement, pathlib.Path)

    try:
        directory_name = sys.argv[1]
        print(f"command line: directory_name={directory_name}")
    except IndexError:
        directory_name = None

    try:
        dir_raw = configSetup.measure_for_all_steps(dir_measurement, directory_name=directory_name)
        return dir_raw
        # run_condense(dir_measurement) # 20200212 Peter, nicht jedes mal, lieber von Hand
        # import run_1_condense # 20200212 Peter, nicht jedes mal, lieber von Hand
        # run_1_condense.run() # 20200212 Peter, nicht jedes mal, lieber von Hand
    except Exception:  # pylint: disable=broad-except
        import traceback

        traceback.print_exc()
        print("Hit any key to terminate")
        sys.stdin.read()


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
