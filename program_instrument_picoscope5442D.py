import sys
import time
import logging

import numpy as np

import program_configsetup
import program_measurement_stream

logger = logging.getLogger("logger")

try:
    import msl.loadlib
except ImportError as ex:
    logger.error(f"Failed to import ({ex}). Try: pip install -r requirements_picoscope.txt")
    logger.exception(ex)
    sys.exit(0)

import msl.equipment  # pylint: disable=wrong-import-position
import msl.equipment.resources.picotech.picoscope  # pylint: disable=wrong-import-position

from msl.equipment.resources.picotech.picoscope import callbacks  # pylint: disable=wrong-import-position


PICSCOPE_MODEL_5442D = "5442D"  # Peter
# PICSCOPE_MODEL_5442D='5444D' # Andre
PICSCOPE_MODEL_2204A = "2204A"
# The picoscope we are going to use
PICSCOPE_MODEL = PICSCOPE_MODEL_5442D

if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
    PICSCOPE_ADDRESS = "SDK::ps5000a"
    ALL_CHANNELS = ("A", "B", "C", "D")

if PICSCOPE_MODEL == PICSCOPE_MODEL_2204A:
    # The implementation of the 2204A is a hack. The instrument initializes and measures.
    # However the returned measurements are not evaluated.
    # Setting up dt_s and desired_sample_time_s seems to be buggy!
    PICSCOPE_ADDRESS = "SDK::ps2000"
    ALL_CHANNELS = ("A", "B")


class Instrument:
    def __init__(self, configstep):
        self.streaming_done = False
        self.actual_sample_count = 0
        self.scope = None

        self.record = msl.equipment.EquipmentRecord(
            manufacturer="Pico Technology",
            model=PICSCOPE_MODEL,
            # serial='GQ903/0003',
            connection=msl.equipment.ConnectionRecord(
                backend=msl.equipment.Backend.MSL,
                address=PICSCOPE_ADDRESS,
                # properties={'open_async': True},  # opening in async mode is done in the properties
                properties=dict(
                    resolution=configstep.resolution,
                    # resolution='15bit',
                    # resolution='16bit',  # only used for ps5000a series PicoScope's
                    auto_select_power=False,  # for PicoScopes that can be powered by an AC adaptor or by a USB cable
                ),
            ),
        )

    def connect(self):
        for retry in range(1000):
            try:
                self.scope = self.record.connect()  # establish a connection to the PicoScope
                info = self.scope.get_unit_info()
                # logger.debug(f'picoscope info={info}')
                break
            except msl.equipment.exceptions.PicoTechError as ex:
                logging.exception(ex)
                if retry >= 3:
                    raise

    def close(self):
        # self.scope.set_data_buffer(configstep.input_channel)
        self.scope.disconnect()

    def calculate_dt_s(self, configstep, max_samples_bytes):
        # Given: configstep.duration_s
        # Required: selected_dt_s
        # Limited by: self.scope.set_timebase
        # Limited by: Maximum filesize

        # Programmers Guide "3.6 Timebases", only one channel_raw
        assert configstep.dt_s is not None
        selected1_dt_s = configstep.dt_s
        if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
            max_sampling_rate = 62.5e6
            desired_sample_time_s = max_samples_bytes * selected1_dt_s
        if PICSCOPE_MODEL == PICSCOPE_MODEL_2204A:
            max_sampling_rate = 10e5
            selected1_dt_s = 2.0 / max_sampling_rate
            desired_sample_time_s = 5000 * selected1_dt_s

        max_samples = 67108608  # On Peters 5442D
        desired_sample_time_max_s = max_samples * selected1_dt_s
        if desired_sample_time_s > desired_sample_time_max_s:
            logger.info(f"Avoid buffer getting too big: reducing sample time from {desired_sample_time_s:0.1f} to {desired_sample_time_max_s:0.1f}s!")
            desired_sample_time_s = desired_sample_time_max_s

        selected2_dt_s, _num_samples = self.scope.set_timebase(selected1_dt_s, desired_sample_time_s)  # sample the voltage on Channel A every 1 us, for 100 us

        assert configstep.dt_s is not None
        if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
            # assert math.isclose(selected2_dt_s, configstep.dt_s), f'selected2_dt_s {selected2_dt_s} != configstep.dt_s {configstep.dt_s}'
            assert 0.9 < (selected2_dt_s / configstep.dt_s) < 1.1, f"selected2_dt_s {selected2_dt_s} != configstep.dt_s {configstep.dt_s}"

        return selected2_dt_s
        # logger.debug(f'configstep.duration_s={configstep.duration_s:.4e}, total_samples={total_samples}, total_samples*selected_dt_s={total_samples*selected_dt_s:.4e}')
        # logger.debug(f'set_timebase({desired_dt_s:.4e}) -> {selected_dt_s:.4e}')
        # total_samples_before = total_samples
        # total_samples = int(configstep.duration_s/selected_dt_s)
        # logger.debug(f'total_samples={total_samples_before}) -> {total_samples}')

    def acquire(self, configstep, stream_output, filelock_measurement):  # pylint: disable=too-many-statements
        assert isinstance(configstep, program_configsetup.ConfigStep)

        valid_ranges = set(range.value for range in self.scope.enRange)
        assert configstep.input_Vp.value in valid_ranges

        assert configstep.input_channel in ALL_CHANNELS

        for channel_raw in ALL_CHANNELS:
            enabled = channel_raw in configstep.input_channel
            self.scope.set_channel(channel_raw, coupling="dc", bandwidth=configstep.bandwitdth, offset=configstep.offset, scale=configstep.input_Vp, enabled=enabled)

        if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
            max_samples_bytes = self.scope.memory_segments(num_segments=1)
        else:
            max_samples_bytes = 1024 * 1024

        dt_s = self.calculate_dt_s(configstep, max_samples_bytes)
        total_samples = int(configstep.duration_s / dt_s)
        logger.info(f"Aquisition with dt_s {dt_s:.3E}s, fs {1.0/dt_s:.3E}Hz")

        # PicoScope 6
        # 8ns
        # 125MS/s
        # 250000 Samples
        # 15bits

        # a, b = self.scope.get_timebase(timebase=4, num_samples=250000)

        # resolution_ = self.scope.enDeviceResolution.RES_15BIT
        # channels_ = self.scope.enChannelFlags.A + self.scope.enChannelFlags.B
        # timebaseA_, time_interval_nanosecondsA_ = self.scope.get_minimum_timebase(resolution_, channels_)
        # # timebaseA_=3, time_interval_nanosecondsA_=8e-09

        # resolution_ = self.scope.enDeviceResolution.RES_16BIT
        # channels_ = self.scope.enChannelFlags.A
        # timebaseB_, time_interval_nanosecondsB_ = self.scope.get_minimum_timebase(resolution_, channels_)
        # # timebaseA_=4, time_interval_nanosecondsA_=1.6e-09

        if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
            # self.scope.set_data_buffer(configstep.input_channel, mode=PS5000ARatioMode.AVERAGE)
            self.scope.set_data_buffer(configstep.input_channel)
        channel = self.scope.channel[configstep.input_channel]

        channel_gain = configstep.skalierungsfaktor * channel._volts_per_adu

        def convert(adu_values):
            volts = np.multiply(channel_gain, adu_values, dtype=np.float32)  # NUMPY_FLOAT_TYPE
            return volts

        stream = program_measurement_stream.InThread(stream_output, dt_s=dt_s, duration_s=configstep.duration_s, func_convert=convert)
        stream.start()

        self.actual_sample_count = 0
        self.streaming_done = False

        if PICSCOPE_MODEL == PICSCOPE_MODEL_2204A:

            @callbacks.GetOverviewBuffersMaxMin
            def my_get_overview_buffer(overviewBuffers, overflow, triggeredAt, triggered, auto_stop, nValues):  # pylint: disable=too-many-arguments
                if False:
                    logger.info(f"StreamingReady Callback: overviewBuffers={overviewBuffers}, overflow={overflow}, auto_stop={auto_stop}, nValues={nValues}")
                if auto_stop:
                    self.streaming_done = True
                    stream.put_EOF()
                    logger.info(r"STOP(time over)")

        if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:

            @callbacks.ps5000aStreamingReady
            def my_streaming_ready(handle, num_samples, start_index, overflow, trigger_at, triggered, auto_stop, p_parameter):  # pylint: disable=too-many-arguments
                if False:
                    logger.info(f"StreamingReady Callback: handle={handle}, num_samples={num_samples}, start_index={start_index}, overflow={overflow}, trigger_at={trigger_at}, " "triggered={triggered}, auto_stop={auto_stop}, p_parameter={p_parameter}")

                # self.stream.put(channel_raw[start_index:start_index+num_samples])
                # See: def volts(self):
                adu_values = channel.raw[start_index : start_index + num_samples]
                queueFull = stream.put(adu_values)
                if queueFull:
                    self.streaming_done = True
                    stream.put_EOF()
                    logger.info("STOP(queue full)")

                if overflow:
                    # logfile.write(f'Overflow: {self.actual_sample_count+start_index}\n')
                    stream.list_overflow.append(self.actual_sample_count + start_index)

                self.actual_sample_count += num_samples

                def stop(reason):
                    self.streaming_done = True
                    stream.put_EOF()
                    logger.info(f"STOP({reason})")

                if filelock_measurement.requested_stop_soft():
                    stop("<ctrl-c> or softstop")

                if self.actual_sample_count > total_samples:
                    stop("time over")

                if overflow:
                    logger.warning("!!! Overflow !!!  Voltage to big at input of picoscope. Change input range.")
                # logger.debug('.', end='')

                assert not auto_stop
                assert not triggered

        start_s = time.time()
        self.scope.run_streaming(auto_stop=False)
        while not self.streaming_done:
            if stream.done:
                break
            # wait until the latest streaming values are ready
            self.scope.wait_until_ready()
            if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
                # get the latest streaming values
                self.scope.get_streaming_latest_values(my_streaming_ready)
            if PICSCOPE_MODEL == PICSCOPE_MODEL_2204A:
                _rc = self.scope.get_streaming_last_values(my_get_overview_buffer)
                # rc==1: if the callback will be called
                # rc==0: if the callback will not be called, either because one of the inputs
                #        is out of range or because there are no samples available

        self.scope.stop()
        self.close()

        logger.info("")
        logger.info(f"Time spent in aquisition {time.time()-start_s:1.1f}s")
        logger.info("Waiting for thread to finish calculations...")
        stream.join()

        logger.info("Done")


# if __name__ == '__main__':
#   pymeas = program.PyMeas2019()

#   picoscope = Instrument()
#   picoscope.connect()
#   for frequency_hz in (1e2, 1e4, 1e6):
#     picoscope.acquire(setup_name='ch1', frequency_hz=frequency_hz, duration_s=5.0, amplitude_Vpp=2.0)
