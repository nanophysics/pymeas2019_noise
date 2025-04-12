# https://github.com/petermaerki/ad_low_noise_float_2023_git/blob/hmaerki/evaluation_software/evaluation_software/cpp_cdc/2025-03-30a_ads127L21/src/reader.py
import serial
import serial.tools.list_ports
import threading
import re
import sys
import time
import typing
import logging
import pathlib

import numpy as np

from . import program_configsetup
from . import program_fir
from . import program_measurement_stream

logger = logging.getLogger("logger")


RE_STATUS_BYTE_MASK = re.compile(r"STATUS_BYTE_MASK=0x(\w+)")


class PcbAd:
    VID = 0x2E8A
    PID = 0x4242
    if sys.platform == "win32":
        DESCRIPTION = "USB Serial Device"
    else:
        DESCRIPTION = "ad_low_noise_float_2023"

    def __init__(self) -> None:
        devices_pcb_ad: list[str] = []
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.pid == self.PID:
                if port.vid == self.VID:
                    if port.description.startswith(self.DESCRIPTION):
                        devices_pcb_ad.append(port.device)

        assert (
            len(devices_pcb_ad) == 2
        ), f"{self.DESCRIPTION} not found: {devices_pcb_ad}"
        self.serial_control = serial.Serial(devices_pcb_ad[0], timeout=1)
        self.serial_adc_measurements = serial.Serial(devices_pcb_ad[1], timeout=1)

    def readline(self) -> str:
        while True:
            line = self.serial_control.readline()
            line = line.strip().decode("ascii")
            if len(line) > 0:  # TODO: Why
                return line

    def close(self) -> None:
        self.serial_control.close()
        self.serial_adc_measurements.close()


class AdcMeasurementsThread(threading.Thread):
    STATUS_BYTE_MASK = 0x76
    IN_SYNC_COUNTER_START = 100

    def __init__(self, serial_adc_measurements: serial.Serial) -> None:
        super().__init__(name="adc_measurements", daemon=False)
        self.serial_adc_measurements = serial_adc_measurements
        self.cb_measurement = lambda acd_value_V: None
        self.stop_flag = False
        self.start()

    def run(self) -> None:
        in_sync_counter = self.IN_SYNC_COUNTER_START
        while not self.stop_flag:
            adc_measurement = self.serial_adc_measurements.read(size=4)
            status = adc_measurement[0]
            in_sync = (status & ~self.STATUS_BYTE_MASK) == 0x00

            if not in_sync:
                print(f"{in_sync=}")
                self.serial_adc_measurements.read(size=1)
                in_sync_counter = self.IN_SYNC_COUNTER_START
                continue

            if in_sync_counter > 0:
                in_sync_counter -= 1
                if in_sync_counter == 0:
                    print(f"{in_sync=}")
                continue

            def signExtend() -> int:
                """
                See: https://github.com/TexasInstruments/precision-adc-examples/blob/42e54e2d3afda165bd265020bac97c8aedf1f135/devices/ads127l21/ads127l21.c#L571-L578
                """
                measurement_raw = 0
                for idx in (1, 2, 3):
                    measurement_raw <<= 8
                    measurement_raw += adc_measurement[idx]

                if measurement_raw & 0x80_00_00:
                    measurement_raw -= 0x1_00_00_00

                return measurement_raw

            def get_adc_value_V(adc_value_int: int) -> float:
                """
                See https://www.ti.com/lit/ds/symlink/ads127l21.pdf
                page 72, 7.5.1.8.1 Conversion Data
                """
                REF_V = 5.0
                GAIN = 5.0  # 1.0, 2.0, 5.0, 10.0

                return adc_value_int / (2**23) * REF_V / GAIN

            adc_value_int = signExtend()
            adc_value_V = get_adc_value_V(adc_value_int)
            self.cb_measurement(adc_value_V)
            # print(f"{adc_value_V=:15.6f} ({adc_value_int})")

    def stop(self) -> None:
        self.stop_flag = True
        self.join(timeout=100)


class Instrument:
    def __init__(self, configstep):
        self.pcb_ad = PcbAd()
        self.adc_measurements_thread = AdcMeasurementsThread(
            serial_adc_measurements=self.pcb_ad.serial_adc_measurements
        )

    def connect(self):
        while True:
            line = self.pcb_ad.readline()
            match_status_byte = RE_STATUS_BYTE_MASK.match(line)
            if match_status_byte:
                status_byte_mask = int(match_status_byte.group(1), base=16)
                assert (
                    self.adc_measurements_thread.STATUS_BYTE_MASK == status_byte_mask
                ), (
                    self.adc_measurements_thread.STATUS_BYTE_MASK,
                    status_byte_mask,
                )
                return

    def close(self):
        self.adc_measurements_thread.stop()
        self.pcb_ad.close()

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


        def convert(values_V):
            return np.array(values_V, dtype=np.float32)

        # stream = program_measurement_stream.InThread(
        #     stream_output,
        #     dt_s=configstep.dt_s,
        #     filename_capture_raw=filename_capture_raw,
        #     duration_s=configstep.duration_s,
        #     func_convert=convert,
        # )
        # stream.start()
        # self.streaming_done = False

        # for i in range(total_samples // trig_count):

        class Measurements:
            def __init__(self) -> None:
                self.count = 0

            def cb(self, adc_value_V: float) -> None:
                self.count += 1
                if self.count % 100_000 == 0:
                    print(
                        f"{self.count} samples of {total_samples} {self.count/total_samples*100:0.0f}%. {adc_value_V=:0.6f}"
                    )
                queueFull = stream_output.push([adc_value_V])
                assert not queueFull

        measurements = Measurements()
        self.adc_measurements_thread.cb_measurement = measurements.cb

        def flush_stages():
            max_calculations = 30
            for _ in range(max_calculations):
                calculation_stage = stream_output.push(None)
                done = len(calculation_stage) == 0
                if done:
                    break

        while True:
            if measurements.count > total_samples:
                flush_stages()
                return
            if filelock_measurement.requested_stop_soft():
                # stop(ExitCode.CTRL_C, "<ctrl-c> or softstop")
                flush_stages()
                return
            line = self.pcb_ad.readline()
            print(line)
            time.sleep(0.1)


def main():
    print(f"Started: {sys.version}")
    instrument = Instrument(configstep=None)
    instrument.connect()

    def cb_measurement(adc_value_V: float) -> None:
        print(f"{adc_value_V=:15.6f}")

    instrument.adc_measurements_thread.cb_measurement = cb_measurement


if __name__ == "__main__":
    main()
