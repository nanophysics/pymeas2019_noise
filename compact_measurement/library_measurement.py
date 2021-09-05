from os import O_RANDOM
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

from library_combinations import Speed, Combination  # pylint: disable=wrong-import-position
from pymeas.library_filelock import ExitCode  # pylint: disable=wrong-import-position

logger = logging.getLogger("logger")

MODULE_CONFIG_FILENAME = library_path.DIR_MEASUREMENT / f"config_{socket.gethostname()}.py"
if not MODULE_CONFIG_FILENAME.exists():
    print(f"ERROR: Missing file: {MODULE_CONFIG_FILENAME.name}")
    sys.exit(1)

MODULE_CONFIG = __import__(MODULE_CONFIG_FILENAME.with_suffix("").name)

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
    config.step_3_slow.duration_s = 11.0 * 60.0 # bei 0.1 Hz noch recht verrauscht, fuer die Beurteilung der Stepsize braucht es mindestens 9 Minuten

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

    # config.step_0_settle.skip = True
    # config.step_1_fast.skip = True
    # config.step_2_medium.skip = True
    # config.step_3_slow.skip = True

    return config
"""


@dataclass
class VoltageMeasurement:
    file: pathlib.Path

    def write(self, value) -> None:
        assert isinstance(value, float)
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(str(value))

    def read(self) -> None:
        if self.file.exists():
            return float(self.file.read_text())
        return None


@dataclass
class MeasurementContext:  # pylint: disable=too-many-instance-attributes
    compact_serial: str
    measurement_date: str
    topdir: pathlib.Path
    compact_pythonpath: str = MODULE_CONFIG.COMPACT_PYTHONPATH
    scanner_pythonpath: str = MODULE_CONFIG.SCANNER_PYTHONPATH
    compact_2012 = None
    scanner_2020 = None
    speed: Speed = Speed.SMOKE
    mocked_scanner: bool = False
    mocked_compact: bool = False
    mocked_picoscope: bool = False
    mocked_voltmeter: bool = False
    mocked_hv_amp: bool = False

    @property
    def stati(self):
        return Stati(self, self.dir_measurement_date / "stati_measurements_done.txt")

    @property
    def dir_measurements(self):
        return self.topdir / "compact_measurements"

    @property
    def dir_measurement_date(self):
        # 20201111_03
        return self.dir_measurements / f"{self.compact_serial}-{self.measurement_date}"


class Measurement:
    def __init__(self, context: MeasurementContext, combination: Combination):
        self.context = context
        self.combination = combination
        self.query_scanner = pyboard_query.BoardQueryPyboard("scanner_pyb_2020")
        self.query_compact = pyboard_query.BoardQueryPyboard("compact_2012")
        self.compact_2012 = None
        self.scanner_2020 = None

        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V/stati_noise_done.txt
        self.stati_meastype_noise = Stati(self.context, self.dir_measurementtype / "stati_noise_done.txt")
        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V/stati_plot_done.txt
        self.stati_meastype_plot = Stati(self.context, self.dir_measurementtype / "stati_plot_done.txt")
        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V/DA01/stati_noise_done.txt
        self.stati_meastype_channel_noise = Stati(self.context, self.dir_measurement_channel / "stati_noise_done.txt")
        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V/DA01/stati_plot_done.txt
        self.stati_meastype_channel_plot = Stati(self.context, self.dir_measurement_channel / "stati_plot_done.txt")

        self.stati_meastype_channel_plot.dependson(self.stati_meastype_channel_noise)
        self.stati_meastype_plot.dependson(self.stati_meastype_noise)
        self.stati_meastype_channel_noise.feeds(self.stati_meastype_noise)
        self.stati_meastype_channel_plot.feeds(self.stati_meastype_plot)

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
            raise Exception(f"Expected compact_2012 with hw_serial={expected_serial}, but {connected_serial} is connected!")

    @property
    def dir_measurementtype(self):
        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V
        return self.context.dir_measurement_date / self.combination.dirpart_measurementtype

    @property
    def dir_measurement_channel(self):
        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V/DA01
        return self.dir_measurementtype / f"raw-{self.combination.channel_color_text}"

    @property
    def measurement_channel_voltage(self):
        # compact_measurements/20000101_01-20201130a/DA_OUT_+10V/DA01/stati_voltage.txt
        return VoltageMeasurement(file=self.dir_measurementtype / f"stati_{self.combination.channel_color_text}_voltage.txt")

    @property
    def config_measurement(self):
        # 20201111_03-DAdirect-10V/DA01
        return self.dir_measurementtype / "config_measurement.py"

    def create_directory(self):
        self.dir_measurementtype.mkdir(parents=True, exist_ok=True)

        dict_template = {
            "TITLE": self.dir_measurementtype.name,
            "input_Vp": self.combination.picoscope_input_Vp,
            "SMOKE": ((self.context.speed != Speed.DETAILED_NO_HV_AMP) and (self.context.speed != Speed.DETAILED_WITH_HV_AMP)),
        }

        config_measurement_text = TEMPLATE.format(**dict_template)
        if not self.config_measurement.exists():
            self.config_measurement.write_text(config_measurement_text)

        # We expect that the file 'config_measurement' always has the same content
        if config_measurement_text != self.config_measurement.read_text():
            logger.error(f"Contents changed: {self.config_measurement}")

        self.copy_file_templates()

    def copy_file_templates(self):
        # Copy the requires file templates
        directory_measurement_actual = library_path.TOPDIR / "measurement-actual"
        for filename in directory_measurement_actual.glob("*.*"):
            if filename.name == "config_measurement.py":
                # To not overwrite 'config_measurement.py'!
                continue
            if filename.suffix in (".bat", ".py"):
                shutil.copyfile(filename, self.dir_measurementtype / filename.name)

    def _add_pythonpath(self, pythonpath):
        path = pathlib.Path(pythonpath).absolute()
        assert path.exists()
        assert path.is_dir()
        sys.path.insert(0, str(path))

    def _log_temperature(self):
        if self.scanner_2020:
            temp_C = self.scanner_2020.measure_temp_C()
            logger.info(f"Temperature on scanner {temp_C:0.3f}C")

    def configure(self, voltage=False, density=False):
        assert voltage != density

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
                dict_requested_values[dac] = {"f_DA_OUT_desired_V": 0.0}
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
            if voltage:
                # Spannung mit dem Multimeter messen
                self.scanner_2020.boards[1].set(20)

        if not self.context.mocked_compact:
            # compact: DA voltage
            dict_requested_values[self.combination.channel0] = {"f_DA_OUT_desired_V": self.combination.f_DA_OUT_desired_V}
            self.compact_2012.sync_dac_set_all(dict_requested_values)

    def measure_voltage(self):
        if self.context.mocked_voltmeter:
            self.measurement_channel_voltage.write(47.11)
            return
        import pyvisa as visa  # pylint: disable=import-error

        connection = "GPIB0::12::INSTR"
        rm = visa.ResourceManager()
        try:
            rm.list_resources()
            AVERAGE_COUNT = 8
            instrument = rm.open_resource(connection)
            instrument.timeout = 5000
            instrument.write("*RST")
            instrument.write("*CLS")
            instrument.write("CONF:VOLT:DC")
            instrument.write("INP:IMP:AUTO ON")
            instrument.write("VOLT:DC:NPLC 10")  # NPLC: Integration over powerlinecycles, 0.02 0.2 1 10 100
            instrument.write("TRIG:SOUR IMM")

            for i in range(30):  # voltage has to settle, low pass filter in some configurations, discard first measurements
                string = instrument.query("READ?")
                # logger.debug(f"Discard first values, Voltage {float(string):.10f} V")
            voltage = 0.0
            for i in range(AVERAGE_COUNT):
                string = instrument.query("READ?")
                voltage += float(string)
                # logger.debug(f"Voltmeter: Measurement {i}  Spannung {float(string):.10f} V")
            voltage = voltage / float(AVERAGE_COUNT)
            # logger.debug(f"Voltmeter: Average: {voltage:.10f} V")
            self.measurement_channel_voltage.write(voltage)
            instrument.close()
        except visa.VisaIOError as e:
            logger.error(f"Error connecting {connection}: {e}")
            logger.error(f"Available devices {rm.list_resources()}")
            raise

    def measure_density(self):
        if self.context.mocked_picoscope:
            return

        self._log_temperature()

        retry = 0
        while True:
            try:
                self.subprocess(cmd="run_0_measure.py", arg=self.dir_measurement_channel.name, logfile=self.dir_measurement_channel / "logger_measurement.txt")
                self._log_temperature()
                break
            except Exception as ex:  # pylint: disable=broad-except
                logger.error(f"Failed to measure: {ex}")
                self._log_temperature()
                if retry >= 3:
                    raise
                retry += 1
                time.sleep(5)
                logger.error(f"Retry {retry}")

    # def _copy_file(self, filename):
    #     assert isinstance(filename, str)
    #     # Redundant - may be removed...
    #     shutil.copyfile(library_path.TOPDIR / "measurement-actual" / filename, self.dir_measurementtype / filename)

    def channel_plot(self):
        return self.subprocess(cmd="run_1_condense.py", arg=self.dir_measurement_channel.name, logfile=self.dir_measurement_channel / "logger_condense.txt")

    def meastype_plot(self):
        return self.subprocess(cmd="run_1_condense.py", arg="TOPONLY", logfile=self.dir_measurementtype / "logger_condense.txt")

    def subprocess(self, cmd: str, arg: str, logfile: pathlib.Path):
        # self._copy_file(filename="library_path.py")
        # self._copy_file(filename=cmd)
        self.copy_file_templates()

        rc = subprocess.call([sys.executable, cmd, arg], cwd=str(self.dir_measurementtype), creationflags=subprocess.CREATE_NEW_CONSOLE)
        if rc == ExitCode.OK.value:
            return
        if rc == ExitCode.CTRL_C.value:
            ExitCode.CTRL_C.os_exit(f'Pressed <ctrl-c> in "{cmd} {arg}". See logfile: {str(logfile)}')
            return
        raise Exception(f'Command to "{cmd} {arg}" returned {rc}. See logfile: {str(logfile)}')
