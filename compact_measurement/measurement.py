import sys
import time
import shutil
import logging
import socket
import pathlib
import subprocess
from dataclasses import dataclass

from mp import pyboard_query
import library_path

from combinations import Speed, Environment, Combination, Combinations

EXTERN_MEASUREMENT_PROCESS = True

TEMPLATE = """
TITLE = "{TITLE}"

def get_configsetup():
    from pymeas import program_config_instrument_picoscope

    config = program_config_instrument_picoscope.get_config_setupPS500A()

    config.step_0_settle.settle = True
    config.step_0_settle.settle_time_ok_s = 40.0
    config.step_0_settle.duration_s = config.step_0_settle.settle_time_ok_s + 8.0 * 60.0 # maximale Zeit bis Fehler
    config.step_0_settle.settle_input_part = 0.5
    #config.step_3_slow.duration_s = 5.0 * 60.0 # bei 0.1 Hz noch recht verrauscht
    config.step_3_slow.duration_s = 10.0 * 60.0 # bei 0.1 Hz noch recht verrauscht

    if {SMOKE}:
        # Smoke test: Reduce times to a minimum
        config.step_0_settle.settle_time_ok_s = 40.0
        config.step_0_settle.duration_s = config.step_0_settle.settle_time_ok_s + 4.0 * 60.0 # maximale Zeit bis Fehler
        #config.step_1_fast.duration_s = 0.2
        #config.step_2_medium.duration_s = 0.5
        config.step_3_slow.duration_s = 0.5 * 60.0

    for step in config.configsteps:
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        step.input_Vp = {input_Vp}
        step.skalierungsfaktor = 1.0e-3
    return config
"""


TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()

from pymeas import library_logger  # pylint: disable=wrong-import-position
logger = logging.getLogger(library_logger.LOGGER_NAME)


MODULE_CONFIG_FILENAME = DIR_MEASUREMENT /  f"config_{socket.gethostname()}.py"
if not MODULE_CONFIG_FILENAME.exists():
    print(f"ERROR: Missing file: {MODULE_CONFIG_FILENAME.name}")
    sys.exit(1)

MODULE_CONFIG = __import__(MODULE_CONFIG_FILENAME.with_suffix('').name)

@dataclass
class MeasurementContext:  # pylint: disable=too-many-instance-attributes
    compact_serial: str
    measurement_date: str
    topdir: pathlib.Path = TOPDIR
    compact_pythonpath: str = MODULE_CONFIG.COMPACT_PYTHONPATH
    scanner_pythonpath: str = MODULE_CONFIG.SCANNER_PYTHONPATH
    compact_2012 = None
    scanner_2020 = None
    speed: Speed = Speed.SMOKE
    environment: Environment = Environment.MOCKED

    @property
    def dirpart(self):
        # 20201111_03
        return f"{self.compact_serial}-{self.measurement_date}"

    @property
    def dir_measurements(self):
        return self.topdir / 'compact_measurements'

@dataclass
class Stati:
    topdir: pathlib.Path
    filename: pathlib.Path

    def commit(self):
        # logger.info(f'    commit(): {self.filename.relative_to(self.topdir)}')
        self.filename.write_text('DONE')

    def is_done(self):
        _done = self.filename.exists()
        # if _done:
            # logger.info(f'    is_done(): SKIPPED: File exists {self.filename.relative_to(self.topdir)}')
        return _done

class MeasurementController:
    def __init__(self, context):
        self.context = context
        self.init_logger()

    def init_logger(self):
        # create file handler which logs even debug messages
        self.context.dir_measurements.mkdir(parents=True, exist_ok=True)
        library_logger.init_logger_append(self.context.dir_measurements / 'logger_measurements.txt')

    def run_measurements(self):
        logger.info('****** run_measurements()')
        logger.info(f'  context.dirpart: {self.context.dirpart}')
        logger.info(f'  context.speed: {self.context.speed.name}')
        logger.info(f'  context.environment: {self.context.environment.name}')

        for combination in Combinations(speed=self.context.speed):
            # print(combination)
            with Measurement(self.context, combination) as measurement:
                if measurement.is_done():
                    continue
                logger.info(f'    {measurement.dir_measurement_raw.relative_to(self.context.dir_measurements)}')
                measurement.create_directory()
                measurement.connect_pyboards()
                measurement.configure()
                measurement.measure()
                measurement.commit()

    def run_qualifikation(self):
        logger.info('    run_qualifikation()')

    def run_diagrams(self):
        logger.info('    run_diagrams()')

class Measurement:
    def __init__(self, context: MeasurementContext, combination: Combination):
        self.context = context
        self.combination = combination
        self.query_scanner = pyboard_query.BoardQueryPyboard('scanner_pyb_2020')
        self.query_compact = pyboard_query.BoardQueryPyboard('compact_2012')
        self.compact_2012 = None
        self.scanner_2020 = None
        # 20201111_03-DAdirect-10V/stati_DA01_done.txt
        # f_stati = self._dir_measurement_raw
        # self.stati = Stati(f_stati.with_name(f"stati_{f_stati.name}_measurement_done.txt"))

        # 20201111_03-DAdirect-10V/DA01/stati_done.txt
        self.stati = Stati(self.context.dir_measurements, self.dir_measurement_raw / "stati_measurement_done.txt")

    def __enter__(self):
        return self

    def __exit__(self, _type, value, tb):
        self.close()

    def is_done(self):
        return self.stati.is_done()

    def commit(self):
        return self.stati.commit()

    def close(self):
        if self.query_scanner.board is not None:
            self.query_scanner.board.close()
        if self.query_compact.board is not None:
            self.query_compact.board.close()

    def connect_pyboards(self):
        if self.context.environment in (Environment.MOCKED, Environment.MOCKED_SCANNER_COMPACT):
            return

        pyboard_query.Connect([self.query_compact, self.query_scanner])
        expected_serial = self.context.compact_serial
        connected_serial = self.query_compact.board.identification.HWSERIAL
        if expected_serial != connected_serial:
            raise Exception(f'Expected compact_2012 with hw_serial={expected_serial}, but {connected_serial} is connected!')

    @property
    def dir_measurement(self):
        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V
        return self.context.dir_measurements / self.context.dirpart / self.combination.dirpart

    @property
    def dir_measurement_raw(self):
        # 20201111_03-DAdirect-10V/DA01
        return self.dir_measurement / f"raw-{self.combination.channel_color_text}"

    @property
    def config_measurement(self):
        # 20201111_03-DAdirect-10V/DA01
        return self.dir_measurement / "config_measurement.py"

    def create_directory(self):
        self.dir_measurement.mkdir(parents=True, exist_ok=True)

        dict_template = {
            "TITLE": self.dir_measurement.name,
            "input_Vp": self.combination.picoscope_input_Vp,
            "SMOKE": (self.context.speed == Speed.SMOKE),
        }
        self.config_measurement.write_text(TEMPLATE.format(**dict_template))

    def _add_pythonpath(self, pythonpath):
        path = pathlib.Path(pythonpath).absolute()
        assert path.exists()
        assert path.is_dir()
        sys.path.append(str(path))

    def configure(self):
        if self.context.environment != Environment.REAL:
            return

        self._add_pythonpath(self.context.compact_pythonpath)
        import compact_2012_driver  # pylint: disable=import-error
        self.compact_2012 = compact_2012_driver.Compact2012(board=self.query_compact.board)

        self._add_pythonpath(self.context.scanner_pythonpath)
        import scanner_pyb_2020  # pylint: disable=import-error
        self.scanner_2020 = scanner_pyb_2020.ScannerPyb2020(board=self.query_scanner.board)
        self.scanner_2020.reset()

        # in order to protect the preamplifyer_noise_2020 one should discharge the inputcapacitor
        # compact: all compact DA voltages to 0V
        dict_requested_values = {}
        for dac in range(10):
            dict_requested_values[dac] = {'f_DA_OUT_desired_V': 0.0}
        self.compact_2012.sync_dac_set_all(dict_requested_values)

        # pyb_scanner: to B19, connected to a 2k2 Resistor. Together with the preamplifyer capacitor of 100uF we get a timeconstant of 0.22s.
        self.scanner_2020.boards[1].set(19)
        resistor_B19 = 2200.0
        capacitor_preamplifyer_noise_2020_F = 100e-6
        wait_s = 5.0 * resistor_B19 * capacitor_preamplifyer_noise_2020_F
        time.sleep(wait_s)
        # pyb_scanner: disconnect
        self.scanner_2020.reset()
        # pyb_scanner: now connect
        self.combination.configure_pyscan(self.scanner_2020)

        # compact: DA voltage
        dict_requested_values[self.combination.channel0] = {'f_DA_OUT_desired_V': self.combination.f_DA_OUT_desired_V}
        self.compact_2012.sync_dac_set_all(dict_requested_values)

    def measure(self):
        if self.context.environment in (Environment.MOCKED,):
            return

        if EXTERN_MEASUREMENT_PROCESS:
            # Copy the requires file templates
            directory_measurement_actual = TOPDIR / 'measurement-actual'
            for filename in directory_measurement_actual.glob('*.*'):
                if filename.name == 'config_measurement.py':
                    # To not overwrite 'config_measurement.py'!
                    continue
                if filename.suffix in ('.bat', '.py'):
                    shutil.copyfile(filename, self.dir_measurement / filename.name)

            logger.info(f"Measure {self.dir_measurement_raw.relative_to(self.context.topdir)}")
            subprocess.check_call([sys.executable, "run_0_measure.py", self.dir_measurement_raw.name], cwd=str(self.dir_measurement), creationflags=subprocess.CREATE_NEW_CONSOLE)
            return

        # TODO(hans): Obsolete: Remove
        self._add_pythonpath(self.context.topdir / "libraries" / "msl-equipment")

        # pylint: disable=wrong-import-position,unused-import
        from pymeas import program_config_instrument_picoscope
        from pymeas import program_measure, library_topic, library_plot

        source = self.config_measurement.read_text()
        code = compile(source, str(self.config_measurement), 'exec')
        global_vars = {}
        local_vars = {}
        exec(code, global_vars, local_vars)  # pylint: disable=exec-used
        configsetup = local_vars['get_configsetup']()
        configsetup.validate()

        program_measure.measure2(configsetup, dir_raw=self.dir_measurement_raw)
        plotData = library_topic.PlotDataMultipleDirectories(topdir=self.dir_measurement)
        plotFile = library_plot.PlotFile(plotData=plotData, write_files_directory=self.dir_measurement, title=self.dir_measurement.name)
        plotFile.plot_presentations()
