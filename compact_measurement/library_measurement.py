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
from library_stati import Stati

from library_combinations import Speed, Combination

TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()

from pymeas.library_filelock import ExitCode  # pylint: disable=wrong-import-position
from pymeas import library_logger  # pylint: disable=wrong-import-position

logger = logging.getLogger(library_logger.LOGGER_NAME)

MODULE_CONFIG_FILENAME = DIR_MEASUREMENT /  f"config_{socket.gethostname()}.py"
if not MODULE_CONFIG_FILENAME.exists():
    print(f"ERROR: Missing file: {MODULE_CONFIG_FILENAME.name}")
    sys.exit(1)

MODULE_CONFIG = __import__(MODULE_CONFIG_FILENAME.with_suffix('').name)

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
        config.step_0_settle.settle_time_ok_s = 5.0
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
    mocked_scanner: bool = False
    mocked_compact: bool = False
    mocked_picoscope: bool = False

    @property
    def dir_measurement_date(self):
        # 20201111_03
        return self.dir_measurements / f"{self.compact_serial}-{self.measurement_date}"

    @property
    def dir_measurements(self):
        return self.topdir / 'compact_measurements'

class Measurement:
    def __init__(self, context: MeasurementContext, combination: Combination):
        self.context = context
        self.combination = combination
        self.query_scanner = pyboard_query.BoardQueryPyboard('scanner_pyb_2020')
        self.query_compact = pyboard_query.BoardQueryPyboard('compact_2012')
        self.compact_2012 = None
        self.scanner_2020 = None
        # 20201111_03-DAdirect-10V/DA01/stati_measurement_done.txt
        self.stati_measurement = Stati(self.context.dir_measurements, self.dir_measurement_channel / "stati_measurement_done.txt")
        self.stati_plot = Stati(self.context.dir_measurements, self.dir_measurementtype / "stati_plot_done.txt")

    def __enter__(self):
        return self

    def __exit__(self, _type, value, tb):
        self.close()

    def close(self):
        if self.query_scanner.board is not None:
            self.query_scanner.board.close()
        if self.query_compact.board is not None:
            self.query_compact.board.close()

    def connect_pyboards(self):
        query = []
        if not self.context.mocked_compact:
            query.append(self.query_compact)
        if not self.context.mocked_scanner:
            query.append(self.query_scanner)
        if len(query) == 0:
            return
        pyboard_query.Connect(query)
        expected_serial = self.context.compact_serial
        connected_serial = self.query_compact.board.identification.HWSERIAL
        if expected_serial != connected_serial:
            raise Exception(f'Expected compact_2012 with hw_serial={expected_serial}, but {connected_serial} is connected!')

    @property
    def dir_measurementtype(self):
        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V
        return self.context.dir_measurement_date / self.combination.dirpart_measurementtype

    @property
    def dir_measurement_channel(self):
        # 20201111_03-DAdirect-10V/DA01
        return self.dir_measurementtype / f"raw-{self.combination.channel_color_text}"

    @property
    def config_measurement(self):
        # 20201111_03-DAdirect-10V/DA01
        return self.dir_measurementtype / "config_measurement.py"

    def create_directory(self):
        self.dir_measurementtype.mkdir(parents=True, exist_ok=True)

        dict_template = {
            "TITLE": self.dir_measurementtype.name,
            "input_Vp": self.combination.picoscope_input_Vp,
            "SMOKE": (self.context.speed == Speed.SMOKE),
        }

        config_measurement_text = TEMPLATE.format(**dict_template)
        if not self.config_measurement.exists():
            self.config_measurement.write_text(config_measurement_text)

        # We expect that the file 'config_measurement' always has the same content
        if config_measurement_text != self.config_measurement.read_text():
            logger.error(f'Contents changed: {self.config_measurement}')

    def _add_pythonpath(self, pythonpath):
        path = pathlib.Path(pythonpath).absolute()
        assert path.exists()
        assert path.is_dir()
        sys.path.append(str(path))

    def configure(self):
        if not self.context.mocked_compact:
            self._add_pythonpath(self.context.compact_pythonpath)
            import compact_2012_driver  # pylint: disable=import-error
            self.compact_2012 = compact_2012_driver.Compact2012(board=self.query_compact.board)

        if not self.context.mocked_scanner:
            self._add_pythonpath(self.context.scanner_pythonpath)
            import scanner_pyb_2020  # pylint: disable=import-error
            self.scanner_2020 = scanner_pyb_2020.ScannerPyb2020(board=self.query_scanner.board)
            self.scanner_2020.reset()

        if not self.context.mocked_compact:
            # in order to protect the preamplifyer_noise_2020 one should discharge the inputcapacitor
            # compact: all compact DA voltages to 0V
            dict_requested_values = {}
            for dac in range(10):
                dict_requested_values[dac] = {'f_DA_OUT_desired_V': 0.0}
            self.compact_2012.sync_dac_set_all(dict_requested_values)

        if not self.context.mocked_scanner:
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

        if not self.context.mocked_compact:
            # compact: DA voltage
            dict_requested_values[self.combination.channel0] = {'f_DA_OUT_desired_V': self.combination.f_DA_OUT_desired_V}
            self.compact_2012.sync_dac_set_all(dict_requested_values)

        # an dieser Stelle noch self.scanner_2020.boards[1].set(20) und man koennte die Spannung mit dem Multimeter messen.
        # Fuer die picoscope messung muss Relais 20 aber wieder ausgeschaltet sein.
        # Koennte also auch anschliessend an picoscopemessung zusaetzlich relais 20 geschaltet werden.
        # multimeter_hp34401.py

    def measure(self):
        if self.context.mocked_picoscope:
            return

        # Copy the requires file templates
        directory_measurement_actual = TOPDIR / 'measurement-actual'
        for filename in directory_measurement_actual.glob('*.*'):
            if filename.name == 'config_measurement.py':
                # To not overwrite 'config_measurement.py'!
                continue
            if filename.suffix in ('.bat', '.py'):
                shutil.copyfile(filename, self.dir_measurementtype / filename.name)

        logger.info(f"Measure {self.dir_measurement_channel.relative_to(self.context.topdir)}")
        self.subprocess(cmd="run_0_measure.py", arg=self.dir_measurement_channel.name, logfile=self.dir_measurement_channel / 'logger_measurement.txt')

    def plot(self):
        self.subprocess(cmd="run_1_condense.py", arg=self.dir_measurementtype.name, logfile=self.dir_measurementtype / 'logger_condense.txt')

    def subprocess(self, cmd:str, arg:str, logfile:pathlib.Path):
        rc = subprocess.call([sys.executable, cmd, arg], cwd=str(self.dir_measurementtype), creationflags=subprocess.CREATE_NEW_CONSOLE)
        if rc == ExitCode.OK.value:
            return
        if rc == ExitCode.CTRL_C.value:
            ExitCode.CTRL_C.os_exit(f'Pressed <ctrl-c> in "{cmd} {arg}". See logfile: {str(logfile)}')
        logger.error(f'Command to "{cmd} {arg}" returned {rc}. See logfile: {str(logfile)}')
