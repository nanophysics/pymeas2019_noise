# https://github.com/petermaerki/ad_low_noise_float_2023_git/blob/hmaerki/evaluation_software/evaluation_software/cpp_cdc/2025-03-30a_ads127L21/src/reader.py
import dataclasses
import logging
import re
import sys
import time
import typing

import ad_low_noise_float_2023_decoder
import numpy as np
import serial
import serial.tools.list_ports

from . import program_configsetup
from .constants_ad_low_noise_float_2023 import ConfigStepAdLowNoiseFloat2023
from .library_filelock import ExitCode
from .program_fir import UniformPieces

logger = logging.getLogger("logger")


RE_STATUS_BYTE_MASK = re.compile(r"STATUS_BYTE_MASK=0x(\w+)")


class OutOfSyncException(Exception):
    pass


@dataclasses.dataclass
class BcbStatus:
    """
    status: BEGIN=1
    status: PROGRAM=ad_low_noise_float_2023(0.3.3)
    status: REGISTER_FILTER1=0x02
    status: REGISTER_MUX=0x00
    status: SEQUENCE_LEN_MIN=1000
    status: SEQUENCE_LEN_MAX=30000
    status: ERROR_MOCKED=1
    status: ERROR_MOCKED=1
    status: ERROR_ADS127_MOD=2
    status: ERROR_ADS127_ADC=4
    status: ERROR_FIFO=8
    status: ERROR_ADS127_SPI=16
    status: ERROR_ADS127_POR=32
    status: ERROR_ADS127_ALV=64
    status: ERROR_OVLD=128
    status: ERROR_STATUS_J42=256
    status: ERROR_STATUS_J43=512
    status: ERROR_STATUS_J44=1024
    status: ERROR_STATUS_J45=2048
    status: ERROR_STATUS_J46=4096
    status: END=1
    """

    settings: dict[str, str] = dataclasses.field(default_factory=dict)
    error_codes: dict[int, str] = dataclasses.field(default_factory=dict)

    def add(self, line: str) -> None:
        key, value = line.split("=", 1)
        self.add_setting(key.strip(), value.strip())

    def add_setting(self, key: str, value: str) -> None:
        assert isinstance(key, str)
        assert isinstance(value, str)
        self.settings[key] = value

        if key.startswith("ERROR_"):
            try:
                value_int = int(value, 0)
                bit_position = 0
                while value_int > 1:
                    value_int >>= 1
                    bit_position += 1
                self.error_codes[bit_position] = key
            except ValueError:
                logger.warning(f"Invalid error code: {key}={value}")

    def validate(self) -> None:
        assert self.settings["BEGIN"] == "1"
        assert self.settings["END"] == "1"

    def list_errors(self, error_code: int, inclusive_status: bool) -> list[str]:
        """
        Returns a list of error messages for the given error code.
        """
        assert isinstance(error_code, int)
        # return a list of bit positions which are set in error_code
        error_bits = [i for i in range(32) if (error_code & (1 << i)) != 0]

        error_strings = [self.error_codes[bit_position] for bit_position in error_bits]
        if not inclusive_status:
            error_strings = [
                x for x in error_strings if not x.startswith("ERROR_STATUS_")
            ]
        return error_strings

    @property
    def gain_from_jumpers(self) -> float:
        status_J42_J46 = int(self.settings["STATUS_J42_J46"], 0)
        status_J42_J43 = status_J42_J46 & 0b11
        return {
            0: 1.0,
            1: 2.0,  # J42
            2: 5.0,  # J43
            3: 10.0,  # J42, J43
        }[status_J42_J43]


class Adc:
    PRINTF_INTERVAL_S = 10.0
    VID = 0x2E8A
    PID = 0x4242
    MEASURMENT_BYTES = 3
    COMMAND_START = "s"
    COMMAND_STOP = "p"
    COMMAND_MOCKED_ERROR = "e"
    COMMAND_MOCKED_CRC = "c"

    SEQUENCE_LEN_MAX = 30_000
    BYTES_PER_MEASUREMENT = 3
    DECODER_OVERFLOW_SIZE = 4 * BYTES_PER_MEASUREMENT * SEQUENCE_LEN_MAX

    def __init__(self) -> None:
        self.serial = self._open_serial()
        self.success: bool = False
        self.pcb_status = BcbStatus()
        self.decoder = ad_low_noise_float_2023_decoder.Decoder()

    def _open_serial(self) -> serial.Serial:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == self.VID:
                if port.pid == self.PID:
                    return serial.Serial(port=port.device, timeout=1.0)

        raise ValueError(
            f"No board with VID=0x{self.VID:02X} and PID=0x{self.PID:02X} found!"
        )

    def close(self) -> None:
        self.serial.close()

    def drain(self) -> None:
        while True:
            line = self.serial.read()
            if len(line) == 0:
                return

    def read_status(self) -> bool:
        self.success, self.pcb_status = self._read_status_inner()
        self.pcb_status.validate()
        return self.success

    def _read_status_inner(self) -> tuple[bool, BcbStatus]:
        """
        return True on success
        """
        status = BcbStatus()
        while True:
            line_bytes = self.serial.readline()
            if len(line_bytes) == 0:
                return False, status
            line = line_bytes.decode("ascii").strip()
            status.add(line)
            logger.info(f"  status: {line}")
            if line == "END=1":
                return True, status

    def test_usb_speed(self) -> None:
        begin_ns = time.monotonic_ns()
        counter = 0
        while True:
            measurements = self.serial.read(size=1_000_000)
            # print(f"len={len(measurements)/3}")
            self.decoder.push_bytes(measurements)

            while True:
                numpy_array = self.decoder.get_numpy_array()
                if numpy_array is None:
                    print(".", end="")
                    break
                if self.decoder.get_crc() != 0:
                    logger.error(f"ERROR crc={self.decoder.get_crc()}")
                if self.decoder.get_errors() not in (0, 8, 72):
                    logger.error(f"ERROR errors={self.decoder.get_errors()}")

                counter += len(numpy_array)
                duration_ns = time.monotonic_ns() - begin_ns
                logger.info(f"{1e9 * counter / duration_ns:0.1f} SPS")

                # counter += len(measurements) // 3
                # duration_ns = time.monotonic_ns() - begin_ns
                # print(f"{1e9*counter/duration_ns:0.1f} SPS")

        # Pico:197k  PC Peter 96k (0.1% CPU auslasung)

    def iter_measurements(self) -> typing.Iterable[np.ndarray]:
        while True:
            measurements = self.serial.read(size=1_000_000)
            # print(f"len={len(measurements)/3}")
            self.decoder.push_bytes(measurements)

            while True:
                adc_value_ain_signed32 = self.decoder.get_numpy_array()
                if adc_value_ain_signed32 is None:
                    # print(".", end="")
                    if self.decoder.size() > self.DECODER_OVERFLOW_SIZE:
                        msg = "f'Segment overflow! decoder.size {self.decoder.size()} > DECODER_OVERFLOW_SIZE {self.DECODER_OVERFLOW_SIZE}'"
                        # print(msg)
                        raise OutOfSyncException(msg)
                    break
                # counter += len(adc_value_ain_signed32)
                if self.decoder.get_crc() != 0:
                    msg = f"ERROR crc={self.decoder.get_crc()}"
                    # print(msg)
                    raise OutOfSyncException(msg)

                errors = self.decoder.get_errors()
                error_strings = self.pcb_status.list_errors(
                    errors,
                    inclusive_status=False,
                )
                if len(error_strings) > 0:
                    msg = f"ERROR: {errors}: {' '.join(error_strings)}"
                    logger.error(msg)

                # duration_s = time.monotonic() - begin_s
                # if duration_s > self.PRINTF_INTERVAL_S:
                #     print(
                #         f"{adc_value_ain_signed32[0]=:2.6f}  {counter/duration_s:0.1f} SPS"
                #     )
                #     begin_s = time.monotonic()
                #     counter = 0

                yield adc_value_ain_signed32


class Instrument:
    def __init__(self, configstep: ConfigStepAdLowNoiseFloat2023):
        assert isinstance(configstep, ConfigStepAdLowNoiseFloat2023)
        self.configstep = configstep
        self.adc = Adc()

    def _send_command(self, command: str) -> None:
        logger.info(f"send command: {command}")
        command_bytes = f"\n{command}\n".encode("ascii")
        self.adc.serial.write(command_bytes)

    def _send_command_reset(self):
        msg = f"send command reset: {self.configstep.register_filter1!r} {self.configstep.register_mux!r}"
        logger.info(msg)
        command_reset = f"r-{self.configstep.register_filter1:02X}-{self.configstep.register_mux:02X}-{self.configstep.additional_SPI_reads:d}"
        self._send_command(command_reset)

    def connect(self):
        logger.info("Started")
        self._send_command(Adc.COMMAND_STOP)
        self.adc.drain()
        self._send_command_reset()
        self.adc.read_status()
        self._send_command(Adc.COMMAND_START)
        logger.info(f"iter_measurements(): gain={self.adc.pcb_status.gain_from_jumpers:0.3f}")

    def close(self):
        self.adc.close()

    def acquire(
        self,
        configstep: program_configsetup.ConfigStep,
        filename_capture_raw,
        stream_output,
        filelock_measurement,
    ):  # pylint: disable=too-many-statements
        assert isinstance(configstep, program_configsetup.ConfigStep)
        assert isinstance(stream_output, UniformPieces)

        total_samples = int(configstep.duration_s / configstep.dt_s)

        stream_output.init(stage=0, dt_s=configstep.dt_s)

        def flush_stages():
            max_calculations = 30
            for _ in range(max_calculations):
                calculation_stage = stream_output.push(None)
                done = len(calculation_stage) == 0
                if done:
                    break

        def stop(exit_code: ExitCode, reason: str):
            assert isinstance(exit_code, ExitCode)
            assert isinstance(reason, str)
            stream_output.put_EOF(exit_code=exit_code)
            logger.info(f"STOP({reason})")

        actual_sample_count = 0
        printf_interval_s = 10.0
        next_print_s = start_s = time.monotonic() + printf_interval_s
        last_sample_count = 0
        factor = configstep.input_Vp * configstep.skalierungsfaktor / (2**23)
        while True:
            try:
                for adc_value_ain_signed32 in self.adc.iter_measurements():
                    if filelock_measurement.requested_stop_soft():
                        return stop(ExitCode.CTRL_C, "<ctrl-c> or softstop")

                    if actual_sample_count > total_samples:
                        flush_stages()
                        return stop(ExitCode.OK, "time over")

                    # print(adc_value_V)
                    actual_sample_count += len(adc_value_ain_signed32)
                    adc_value_V = np.multiply(
                        factor,
                        adc_value_ain_signed32,
                        dtype=np.float32,
                    )  # NUMPY_FLOAT_TYPE

                    if next_print_s < time.monotonic():
                        if False:
                            # Mock errors to test recovery
                            self._send_command(Adc.COMMAND_MOCKED_CRC)

                        next_print_s += printf_interval_s
                        elements = [
                            f"{adc_value_V[0]:3.6f}V",
                            f"{actual_sample_count / total_samples * 100:0.0f}%",
                            f"{(actual_sample_count - last_sample_count) / printf_interval_s:,.0f}SPS",
                            f"{actual_sample_count:,} samples of {total_samples:,}",
                        ]
                        logger.info(" ".join(elements))
                        last_sample_count = actual_sample_count
                    queueFull = stream_output.push(adc_value_V)
                    assert not queueFull
            except OutOfSyncException as e:
                logger.error(f"OutOfSyncException: {e}")
                bytes_purged = self.adc.decoder.purge_until_and_with_separator()
                logger.info(f"Purged {bytes_purged} bytes!")

                # self.connect()


def main():
    print(f"Started: {sys.version}")
    instrument = Instrument(configstep=None)
    instrument.connect()

    instrument.adc.test_usb_speed()
    return
    for i, adc_value_ain_V in enumerate(instrument.adc.iter_measurements()):
        if i % 100 == 0:
            print(f"{adc_value_ain_V[0]=:1.6f}")

    # instrument.adc.cb_measurement = cb_measurement


if __name__ == "__main__":
    main()
