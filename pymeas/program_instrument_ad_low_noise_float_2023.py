# https://github.com/petermaerki/ad_low_noise_float_2023_git/blob/hmaerki/evaluation_software/evaluation_software/cpp_cdc/2025-03-30a_ads127L21/src/reader.py
import logging
import re
import sys
import time
import typing

import serial
import serial.tools.list_ports
import ad_low_noise_float_2023_decoder
import numpy as np
from .library_filelock import ExitCode

from . import program_configsetup

logger = logging.getLogger("logger")


RE_STATUS_BYTE_MASK = re.compile(r"STATUS_BYTE_MASK=0x(\w+)")


class Adc:
    PRINTF_INTERVAL_S = 10.0
    VID = 0x2E8A
    PID = 0x4242
    MEASURMENT_BYTES = 3
    COMMAND_START = b"s"
    COMMAND_STOP = b"p"

    def __init__(self) -> None:
        self.serial = self._open_serial()

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

    def drain(self) -> bool:
        while True:
            line = self.serial.read()
            if len(line) == 0:
                return

    def read_status(self) -> bool:
        """
        return True on success
        """
        while True:
            line = self.serial.readline()
            if len(line) == 0:
                return False
            line = line.strip().decode("ascii")
            print(f"  status: {line}")
            if line == "END=1":
                return True

    def test_usb_speed(self) -> None:
        begin_ns = time.monotonic_ns()
        counter = 0
        decoder = ad_low_noise_float_2023_decoder.Decoder()
        while True:
            measurements = self.serial.read(size=1_000_000)
            # print(f"len={len(measurements)/3}")
            decoder.push_bytes(measurements)

            while True:
                numpy_array = decoder.get_numpy_array()
                if numpy_array is None:
                    print(".", end="")
                    break
                if decoder.get_crc() != 0:
                    print(f"ERROR crc={decoder.get_crc()}")
                if decoder.get_errors() not in (0, 8, 72):
                    print(f"ERROR errors={decoder.get_errors()}")

                counter += len(numpy_array)
                duration_ns = time.monotonic_ns() - begin_ns
                print(f"{1e9*counter/duration_ns:0.1f} SPS")

                # counter += len(measurements) // 3
                # duration_ns = time.monotonic_ns() - begin_ns
                # print(f"{1e9*counter/duration_ns:0.1f} SPS")

        # Pico:197k  PC Peter 96k (0.1% CPU auslasung)

    def iter_measurements(self) -> typing.Iterable[np.ndarray]:
        # counter = 0
        # begin_s = time.monotonic()

        decoder = ad_low_noise_float_2023_decoder.Decoder()
        while True:
            measurements = self.serial.read(size=1_000_000)
            # print(f"len={len(measurements)/3}")
            decoder.push_bytes(measurements)

            while True:
                adc_value_ain_signed32 = decoder.get_numpy_array()
                if adc_value_ain_signed32 is None:
                    # print(".", end="")
                    break
                # counter += len(adc_value_ain_signed32)
                if decoder.get_crc() != 0:
                    print(f"ERROR crc={decoder.get_crc()}")
                if decoder.get_errors() not in (0, 8, 72):
                    print(f"ERROR errors={decoder.get_errors()}")

                # duration_s = time.monotonic() - begin_s
                # if duration_s > self.PRINTF_INTERVAL_S:
                #     print(
                #         f"{adc_value_ain_signed32[0]=:2.6f}  {counter/duration_s:0.1f} SPS"
                #     )
                #     begin_s = time.monotonic()
                #     counter = 0

                yield adc_value_ain_signed32


class Instrument:
    def __init__(self, configstep):
        self.adc = Adc()

    def connect(self):
        print("Started")
        self.adc.serial.write(Adc.COMMAND_STOP)
        print("drain()")
        self.adc.drain()
        self.adc.serial.write(Adc.COMMAND_STOP)
        print("status()")
        self.adc.read_status()
        self.adc.serial.write(Adc.COMMAND_START)
        print("iter_measurements()")

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
        next_print_s = start_s = time.monotonic()
        printf_interval_s = 10.0
        factor = configstep.input_Vp.V * configstep.skalierungsfaktor / (2**23)
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

            duration_s = time.monotonic() - start_s
            if next_print_s < time.monotonic():
                next_print_s += printf_interval_s
                elements = [
                    f"{adc_value_V[0]:3.6f}V",
                    f"{actual_sample_count/total_samples*100:0.0f}%",
                    f"{actual_sample_count/duration_s:,.0f}SPS",
                    f"{actual_sample_count:,} samples of {total_samples:,}",
                ]
                print(" ".join(elements))
            queueFull = stream_output.push(adc_value_V)
            assert not queueFull


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
