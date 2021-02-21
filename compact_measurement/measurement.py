import sys
import pathlib
from dataclasses import dataclass

from mp import pyboard_query

from combinations import Combination

TEMPLATE = """
TITLE = "{TITLE}"

def get_configsetup():
    from pymeas import program_config_instrument_picoscope

    config = program_config_instrument_picoscope.get_config_setupPS500A()

    duration_slow_s = 48 * 3600.0
    config.step_0_settle.settle_time_ok_s = duration_slow_s
    config.step_0_settle.duration_s = 30.0 * duration_slow_s
    config.step_0_settle.settle_input_part = 0.5
    for step in config.configsteps:
        # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
        step.input_Vp = {input_Vp}
        step.skalierungsfaktor = 1.0e-3
    return config
"""


@dataclass
class MeasurementContext:
    topdir: pathlib.Path
    compact_serial: str
    measurement_date: str
    compact_pythonpath: str
    scanner_pythonpath: str
    compact_2012 = None
    scanner_2020 = None


    @property
    def dirpart(self):
        # 20201111_03
        return f"{self.compact_serial}-{self.measurement_date}"


class Measurement:
    def __init__(self, context: MeasurementContext, combination: Combination):
        self.context = context
        self.combination = combination
        self.query_scanner = pyboard_query.BoardQueryPyboard('scanner_pyb_2020')
        self.query_compact = pyboard_query.BoardQueryPyboard('compact_2012')

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
        pyboard_query.Connect([self.query_compact, self.query_scanner])
        expected_serial = self.context.compact_serial
        connected_serial = self.query_compact.board.identification.HWSERIAL
        if expected_serial != connected_serial:
            raise Exception(f'Expected compact_2012 with hw_serial={expected_serial}, but {connected_serial} is connected!')

    @property
    def _dir_measurement(self):
        # 20201111_03-DAdirect-10V/DA01
        dirname = f"{self.context.dirpart}_{self.combination.dirpart}"
        return self.context.topdir / dirname

    @property
    def _config_measurement(self):
        # 20201111_03-DAdirect-10V/DA01
        return self._dir_measurement / "config_measurement.py"

    def create_directory(self):
        if not self._dir_measurement.exists():
            self._dir_measurement.mkdir(parents=True, exist_ok=False)

        if not self._config_measurement.exists():
            dict_template = {
                "TITLE": self._dir_measurement.name,
                "input_Vp": "program_config_instrument_picoscope.InputRange.R_100mV",
            }
            self._config_measurement.write_text(TEMPLATE.format(**dict_template))

        dir_raw = self._dir_measurement / self.combination.channel_text
        dir_raw.mkdir(parents=False, exist_ok=True)
        print(self._dir_measurement.name + '/' + dir_raw.name)

    def _add_pythonpath(self, pythonpath):
        path = pathlib.Path(pythonpath).absolute()
        assert path.exists()
        assert path.is_dir()
        sys.path.append(str(path))

    def configure_compact(self):
        self._add_pythonpath(self.context.compact_pythonpath)
        import compact_2012_driver
        self.compact_2012 = compact_2012_driver.Compact2012(board=self.query_compact.board)
        # TODO(hans): Uncomment
        # self.compact_2012.sync_calib_raw_init()

        # dict_requested_values = {
        #     0: # Optional. The DAC [0..9]
        #         {
        #             'f_DA_OUT_desired_V': 5.5, # The value to set
        #             'f_DA_OUT_sweep_VperSecond': 0.1, # Optional
        #             'f_gain': 0.5, # Optional. f_DA_OUT_desired_V=f_dac_desired_V*f_gain
        #         }
        # }

        # return: b_done, {
        #     0: 5.1, # Actual value DA_OUT
        # }

        # This method will receive try to set the values of the dacs.
        # If the call is following very shortly after the last call, it may delay before setting the DACs.
        # If required, f_DA_OUT_sweep_VperSecond will be used for small voltage increments.
        # The effective set values will be returned. To be used for updateing the display and the log output.
        # If b_done == False, the labber driver muss call this method again with the same parameters.

        # dict_requested_values = {
        #     0: # Optional. The DAC [0..9]
        #         {
        #             'f_DA_OUT_desired_V': 5.5, # The value to set
        #             'f_DA_OUT_sweep_VperSecond': 0.1, # Optional
        #             'f_gain': 0.5, # Optional. f_DA_OUT_desired_V=f_dac_desired_V*f_gain
        #         }
        # }

        # b_done, dict_changed_values = self.compact_2012.sync_dac_set_all(dict_requested_values)

        # _iADC24, _fADC24_V = self.compact_2012.sync_calib_read_ADC24(iDac_index=2)

    def configure_pyscan(self):
        self._add_pythonpath(self.context.scanner_pythonpath)
        import scanner_pyb_2020
        self.scanner_2020 = scanner_pyb_2020.ScannerPyb2020(board=self.query_scanner.board)
        self.scanner_2020.reset()

    def measure(self):
        self.scanner_2020.boards[0].set(9)
        dict_requested_values = {
            0: # Optional. The DAC [0..9]
                {
                    'f_DA_OUT_desired_V': 5.5, # The value to set
                    'f_DA_OUT_sweep_VperSecond': 0.1, # Optional
                    'f_gain': 0.5, # Optional. f_DA_OUT_desired_V=f_dac_desired_V*f_gain
                }
        }

        b_done, dict_changed_values = self.compact_2012.sync_dac_set_all(dict_requested_values)

        self._add_pythonpath(self.context.topdir / "libraries" / "msl-equipment")

        # pylint: disable=wrong-import-position
        from pymeas import program_config_instrument_picoscope
        from pymeas import program_measure

        def get_configsetup():
            config = program_config_instrument_picoscope.get_config_setupPS500A()

            duration_slow_s = 48 * 3600.0
            config.step_0_settle.settle_time_ok_s = duration_slow_s
            config.step_0_settle.duration_s = 30.0 * duration_slow_s
            config.step_0_settle.settle_input_part = 0.5
            for step in config.configsteps:
                # To choose the best input range, see the description in 'program_config_instrument_picoscope'.
                step.input_Vp = program_config_instrument_picoscope.InputRange.R_100mV
                step.skalierungsfaktor = 1.0e-3
            return config

        # TOPDIR, DIR_MEASUREMENT = library_path.find_append_path()
        source = self._config_measurement.read_text()
        code = compile(source, str(self._config_measurement), 'exec')
        global_vars = {}
        local_vars = {}
        exec(code, global_vars, local_vars)
        configsetup = local_vars['get_configsetup']()
        configsetup.validate()

        program_measure.measure(configsetup, dir_measurement=self._dir_measurement)

    def commit(self):
        pass
