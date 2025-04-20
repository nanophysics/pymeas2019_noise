# https://github.com/petermaerki/ad_low_noise_float_2023_git/blob/hmaerki/evaluation_software/evaluation_software/cpp_cdc/2025-03-30a_ads127L21/src/reader.py
import serial
import serial.tools.list_ports
import re
import sys
import time
import logging
import typing
import numpy as np

from . import program_configsetup

logger = logging.getLogger("logger")


RE_STATUS_BYTE_MASK = re.compile(r"STATUS_BYTE_MASK=0x(\w+)")


class Adc:
    PRINTF_INTERVAL_S = 2.0
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
                    return serial.Serial(port=port.device, timeout=0.5)

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

    def iter_measurements(self) -> typing.Iterable[float]:
        counter = 0
        counter_separator = 0
        begin_s = time.monotonic()
        running_crc = 0
        STATUS_BYTE = False
        while True:
            measurement = self.serial.read(size=self.MEASURMENT_BYTES)
            if len(measurement) != self.MEASURMENT_BYTES:
                if len(measurement) == 0:
                    return
                raise ValueError(f"Wrong size {measurement}!")

            # TODO: Sync if not aligned!

            measurement_raw_unsigned = 0
            for idx in (0, 1, 2):
                measurement_raw_unsigned <<= 8
                running_crc ^= measurement[idx]
                measurement_raw_unsigned += measurement[idx]

            if STATUS_BYTE:
                byte_status, byte_crc, byte_reserve = measurement
                show = (byte_status != 0) or (running_crc != 0)
                if show:
                    print(
                        f"{counter_separator=} status=0x{byte_status:02X} crc=0x{byte_crc:02X} (0x{running_crc:02X}) reserve=0x{byte_reserve:02X}"
                    )
                counter_separator = 0
                running_crc = 0
                STATUS_BYTE = False
                continue

            if measurement_raw_unsigned == 0:
                STATUS_BYTE = True
                continue

            def signExtend(measurement_raw_unsigned) -> int:
                """
                See: https://github.com/TexasInstruments/precision-adc-examples/blob/42e54e2d3afda165bd265020bac97c8aedf1f135/devices/ads127l21/ads127l21.c#L571-L578
                """
                if measurement_raw_unsigned & 0x80_00_00:
                    measurement_raw_unsigned -= 0x1_00_00_00

                return measurement_raw_unsigned

            def get_adc_value_V(measurement_raw_signed: int) -> float:
                """
                See https://www.ti.com/lit/ds/symlink/ads127l21.pdf
                page 72, 7.5.1.8.1 Conversion Data
                """
                REF_V = 5.0
                GAIN = 5.0  # 1.0, 2.0, 5.0, 10.0

                return measurement_raw_signed / (2**23) * REF_V / GAIN

            measurement_raw_signed = signExtend(measurement_raw_unsigned)
            adc_value_ain_V = get_adc_value_V(measurement_raw_signed)

            counter_separator += 1
            counter += 1
            duration_s = time.monotonic() - begin_s
            if duration_s > self.PRINTF_INTERVAL_S:
                duration_s = time.monotonic() - begin_s
                print(
                    f"{adc_value_ain_V=:2.6f} ({measurement_raw_signed}) {counter/duration_s:0.1f} SPS"
                )
                begin_s = time.monotonic()
                counter = 0

            yield adc_value_ain_V


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

        count = 0
        start_s = time.monotonic()
        for adc_value_ain_V in self.adc.iter_measurements():
            if count > total_samples:
                flush_stages()
                return
            # print(adc_value_V)
            count += 1
            adc_value_V = (
                adc_value_ain_V * configstep.skalierungsfaktor * configstep.input_Vp.V
            )
            if count % 100_000 == 0:
                duration_s = time.monotonic() - start_s
                print(
                    f"{count} samples of {total_samples} {count/duration_s:0.1f}SPS {count/total_samples*100:0.0f}%. {adc_value_ain_V=:0.6f} {adc_value_V=:0.6f}"
                )
            # array_in = np.array([adc_value_V], dtype=np.float32)
            array_in = [adc_value_V]
            queueFull = stream_output.push(array_in)
            assert not queueFull


def main():
    print(f"Started: {sys.version}")
    instrument = Instrument(configstep=None)
    instrument.connect()

    for i, adc_value_ain_V in enumerate(instrument.adc.iter_measurements()):
        if i % 10000 == 0:
            print(f"{adc_value_ain_V=:1.6f}")

    # instrument.adc.cb_measurement = cb_measurement


if __name__ == "__main__":
    main()
