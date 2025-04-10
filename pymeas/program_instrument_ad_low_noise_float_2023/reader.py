# https://github.com/petermaerki/ad_low_noise_float_2023_git/blob/hmaerki/evaluation_software/evaluation_software/cpp_cdc/2025-03-30a_ads127L21/src/reader.py
import serial
import serial.tools.list_ports
import threading
import re
import sys

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


class AdcMeasurementsThread(threading.Thread):
    STATUS_BYTE_MASK = 0x76
    IN_SYNC_COUNTER_START = 100

    def __init__(self, serial_adc_measurements: serial.Serial) -> None:
        super().__init__(name="adc_measurements", daemon=False)
        self.serial_adc_measurements = serial_adc_measurements
        self.start()

    def run(self) -> None:
        in_sync_counter = self.IN_SYNC_COUNTER_START
        while True:
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
            # print(f"{adc_value_V=:15.6f} ({adc_value_int})")


def main():
    print(f"Started: {sys.version}")
    pcb_ad = PcbAd()
    adc_measurements_thread = AdcMeasurementsThread(
        serial_adc_measurements=pcb_ad.serial_adc_measurements
    )
    while True:
        line = pcb_ad.serial_control.readline()
        line = line.strip().decode("ascii")
        if len(line) > 0:  # TODO: Why
            match_status_byte = RE_STATUS_BYTE_MASK.match(line)
            if match_status_byte:
                status_byte_mask = int(match_status_byte.group(1), base=16)
                assert adc_measurements_thread.STATUS_BYTE_MASK == status_byte_mask, (
                    adc_measurements_thread.STATUS_BYTE_MASK,
                    status_byte_mask,
                )
            print(line)


if __name__ == "__main__":
    main()
