import re
import os
import math
import time
import logging
import numpy as np
import program
import program_measurement_stream

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

import msl.equipment.resources.picotech.picoscope
import msl.equipment

from msl.equipment.resources.picotech.picoscope import callbacks
from msl.equipment.resources.picotech.picoscope.enums import PS5000ARange

PICSCOPE_MODEL_5442D='5442D'
PICSCOPE_MODEL_2204A='2204A'
# The picoscope we are going to use
PICSCOPE_MODEL=PICSCOPE_MODEL_5442D

if PICSCOPE_MODEL==PICSCOPE_MODEL_5442D:
  PICSCOPE_ADDRESS='SDK::ps5000a'
  ALL_CHANNELS = ('A', 'B', 'C', 'D')

if PICSCOPE_MODEL==PICSCOPE_MODEL_2204A:
  # The implementation of the 2204A is a hack. The instrument initializes and measures.
  # However the returned measurements are not evaluated.
  # Setting up dt_s and desired_sample_time_s seems to be buggy!
  PICSCOPE_ADDRESS='SDK::ps2000'
  ALL_CHANNELS = ('A', 'B')

class PicoScope:
  def __init__(self, configStep):
    self.record = msl.equipment.EquipmentRecord(
      manufacturer='Pico Technology',
      model=PICSCOPE_MODEL,
      # serial='GQ903/0003',
      connection=msl.equipment.ConnectionRecord(
        backend=msl.equipment.Backend.MSL,
        address=PICSCOPE_ADDRESS,
        # properties={'open_async': True},  # opening in async mode is done in the properties
        properties=dict(
          resolution=configStep.resolution,
          # resolution='15bit',
          # resolution='16bit',  # only used for ps5000a series PicoScope's
          auto_select_power=False,  # for PicoScopes that can be powered by an AC adaptor or by a USB cable
        )
      )
    )

  def connect(self):
    self.scope = self.record.connect()  # establish a connection to the PicoScope

  def close(self):
    self.scope.disconnect()

  def calculate_dt_s(self, configStep, max_samples_bytes):
    # Given: configStep.duration_s
    # Required: selected_dt_s
    # Limited by: self.scope.set_timebase
    # Limited by: Maximum filesize

    # Programmers Guide "3.6 Timebases", only one channel_raw
    assert configStep.dt_s is not None
    selected1_dt_s = configStep.dt_s
    if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
      max_sampling_rate = 62.5e6
      desired_sample_time_s = max_samples_bytes*selected1_dt_s
    if PICSCOPE_MODEL == PICSCOPE_MODEL_2204A:
      max_sampling_rate = 10e5
      selected1_dt_s = 2.0/max_sampling_rate
      desired_sample_time_s = 5000*selected1_dt_s

    selected2_dt_s, num_samples = self.scope.set_timebase(selected1_dt_s, desired_sample_time_s)  # sample the voltage on Channel A every 1 us, for 100 us

    assert configStep.dt_s is not None
    if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
      # assert math.isclose(selected2_dt_s, configStep.dt_s), f'selected2_dt_s {selected2_dt_s} != configStep.dt_s {configStep.dt_s}'
      assert 0.9 < (selected2_dt_s/configStep.dt_s) < 1.1, f'selected2_dt_s {selected2_dt_s} != configStep.dt_s {configStep.dt_s}'

    return selected2_dt_s
    # print(f'configStep.duration_s={configStep.duration_s:.4e}, total_samples={total_samples}, total_samples*selected_dt_s={total_samples*selected_dt_s:.4e}')
    # print(f'set_timebase({desired_dt_s:.4e}) -> {selected_dt_s:.4e}')
    # total_samples_before = total_samples
    # total_samples = int(configStep.duration_s/selected_dt_s)
    # print(f'total_samples={total_samples_before}) -> {total_samples}')

  def acquire(self, configStep, stream_output):
    assert isinstance(configStep, program.ConfigStep)

    valid_ranges = set(range.value for range in self.scope.enRange)
    assert configStep.input_Vp.value in valid_ranges

    assert configStep.input_channel in ALL_CHANNELS

    for channel_raw in ALL_CHANNELS:
      enabled = channel_raw in configStep.input_channel
      self.scope.set_channel(channel_raw, coupling='dc', bandwidth=configStep.bandwitdth, offset=configStep.offset, scale=configStep.input_Vp, enabled=enabled)

    if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
      max_samples_bytes = self.scope.memory_segments(num_segments=1)
    else:
      max_samples_bytes = 1024*1024

    dt_s = self.calculate_dt_s(configStep, max_samples_bytes)
    total_samples = int(configStep.duration_s/dt_s)
    print(f'Choosen dt_s {dt_s:.3e}s and filesize {total_samples*2}Bytes')

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
      self.scope.set_data_buffer(configStep.input_channel)
    channel = self.scope.channel[configStep.input_channel]

    stream = program_measurement_stream.Stream(stream_output, dt_s=dt_s)
    stream.start()

    self.actual_sample_count = 0
    self.streaming_done = False

    if PICSCOPE_MODEL == PICSCOPE_MODEL_2204A:
      @callbacks.GetOverviewBuffersMaxMin
      def my_get_overview_buffer(overviewBuffers, overflow, triggeredAt, triggered, auto_stop, nValues):
        if False:
          print('StreamingReady Callback: overviewBuffers={}, overflow={}, auto_stop={}, nValues={}'.format(overviewBuffers, overflow, auto_stop, nValues))
        if auto_stop:
          self.streaming_done = True
          stream.put_EOF()
          print(r'\nSTOP(time over)', end='')

    if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
      @callbacks.ps5000aStreamingReady
      def my_streaming_ready(handle, num_samples, start_index, overflow, trigger_at, triggered, auto_stop, p_parameter):
        if False:
          print('StreamingReady Callback: handle={}, num_samples={}, start_index={}, overflow={}, trigger_at={}, '
            'triggered={}, auto_stop={}, p_parameter={}'.format(handle, num_samples, start_index, overflow,
                                    trigger_at, triggered, auto_stop, p_parameter))

        # self.stream.put(channel_raw[start_index:start_index+num_samples])
        # See: def volts(self):
        adu_values = channel.raw[start_index:start_index+num_samples]
        volts = adu_values * channel._volts_per_adu - channel._voltage_offset
        queueFull = stream.put(volts)
        if queueFull:
          self.streaming_done = True
          stream.put_EOF()
          print(r'\nSTOP(queue full)', end='')

        if overflow:
          # logfile.write(f'Overflow: {self.actual_sample_count+start_index}\n')
          stream.list_overflow.append(self.actual_sample_count+start_index)

        self.actual_sample_count += num_samples
        if self.actual_sample_count > total_samples:
          self.streaming_done = True
          stream.put_EOF()
          print(r'\nSTOP(time over)', end='')

        if overflow:
          print(r'\noverflow')
        print('.', end='')

        assert auto_stop == False
        assert triggered == False

    start = time.time()
    self.scope.run_streaming(auto_stop=False)
    while not self.streaming_done:
      # wait until the latest streaming values are ready
      self.scope.wait_until_ready()
      if PICSCOPE_MODEL == PICSCOPE_MODEL_5442D:
        # get the latest streaming values
        self.scope.get_streaming_latest_values(my_streaming_ready)
      if PICSCOPE_MODEL == PICSCOPE_MODEL_2204A:
        rc = self.scope.get_streaming_last_values(my_get_overview_buffer)
        # rc==1: if the callback will be called
        # rc==0: if the callback will not be called, either because one of the inputs
        #        is out of range or because there are no samples available

    print()
    print(f'Time spent in aquisition {time.time()-start:1.1f}s')
    print('Waiting for thread ...')
    stream.join()

    print('Done')
    self.scope.stop()

# if __name__ == '__main__':
#   pymeas = program.PyMeas2019()

#   picoscope = PicoScope()
#   picoscope.connect()
#   for frequency_hz in (1e2, 1e4, 1e6):
#     picoscope.acquire(setup_name='ch1', frequency_hz=frequency_hz, duration_s=5.0, amplitude_Vpp=2.0)