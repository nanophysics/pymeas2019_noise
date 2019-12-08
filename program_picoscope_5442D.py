import re
import os
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

class PicoScope:
  def __init__(self, config):
    self.record = msl.equipment.EquipmentRecord(
      manufacturer='Pico Technology',
      model='5442D',
      # serial='GQ903/0003',
      connection=msl.equipment.ConnectionRecord(
        backend=msl.equipment.Backend.MSL,
        address='SDK::ps5000a',
        # properties={'open_async': True},  # opening in async mode is done in the properties
        properties=dict(
          # resolution='15bit',
          resolution='16bit',  # only used for ps5000a series PicoScope's
          auto_select_power=False,  # for PicoScopes that can be powered by an AC adaptor or by a USB cable
        )
      )
    )

  def connect(self):
    self.scope = self.record.connect()  # establish a connection to the PicoScope

  def calculate_dt_s(self, configSetup, max_samples_bytes):
    # Given: configSetup.duration_s
    # Required: selected_dt_s
    # Limited by: self.scope.set_timebase
    # Limited by: Maximum filesize

    # Programmers Guide "3.6 Timebases", only one channel_raw
    max_sampling_rate = 62.5e6
    min_dt_s = 1.0/max_sampling_rate
    max_filesize_samples = configSetup.max_filesize_bytes/2 # 2 Bytes per Sample
    # filesize_dt_s: The sampling rate for maximal filesize
    filesize_dt_s = configSetup.duration_s/max_filesize_samples
    selected1_dt_s = min_dt_s
    if filesize_dt_s > min_dt_s:
      selected1_dt_s = filesize_dt_s
      print(f'Filesize limits dt_s: {min_dt_s:.3e}s -> {filesize_dt_s:.3e}s')

    selected2_dt_s, num_samples = self.scope.set_timebase(selected1_dt_s, max_samples_bytes*selected1_dt_s)  # sample the voltage on Channel A every 1 us, for 100 us

    return selected2_dt_s
    # print(f'configSetup.duration_s={configSetup.duration_s:.4e}, total_samples={total_samples}, total_samples*selected_dt_s={total_samples*selected_dt_s:.4e}')
    # print(f'set_timebase({desired_dt_s:.4e}) -> {selected_dt_s:.4e}')
    # total_samples_before = total_samples
    # total_samples = int(configSetup.duration_s/selected_dt_s)
    # print(f'total_samples={total_samples_before}) -> {total_samples}')


  def acquire(self, configSetup):
    assert isinstance(configSetup, program.ConfigSetup)

    assert type(configSetup.input_Vp) == self.scope.enRange
    all_channels = ('A', 'B', 'C', 'D')
    assert configSetup.input_channel in all_channels

    for channel_raw in all_channels:
      enabled = channel_raw in configSetup.input_channel
      self.scope.set_channel(channel_raw, coupling='dc', bandwidth='BW_20MHZ', scale=configSetup.input_Vp, enabled=enabled)

    max_samples_bytes = self.scope.memory_segments(num_segments=1)

    dt_s = self.calculate_dt_s(configSetup, max_samples_bytes)
    total_samples = int(configSetup.duration_s/dt_s)
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

    self.scope.set_data_buffer(configSetup.input_channel)
    channel = self.scope.channel[configSetup.input_channel]

    sample_process = program_fir.SampleProcess(fir_count=3)
    stream = program_measurement_stream.Stream(sample_process.output, dt_s=0.01)
    stream.start()

    self.actual_sample_count = 0
    self.streaming_done = False

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
      stream.put(volts)

      if overflow:
        # logfile.write(f'Overflow: {self.actual_sample_count+start_index}\n')
        stream.list_overflow.append(self.actual_sample_count+start_index)

      self.actual_sample_count += num_samples
      if self.actual_sample_count > total_samples:
        self.streaming_done = True
        stream.put_EOF()
        print('STOP', end='')

      if overflow:
        print('\noverflow')
      print('.', end='')

      assert auto_stop == False
      assert triggered == False

    start = time.time()
    self.scope.run_streaming(auto_stop=False)
    while not self.streaming_done:
      self.scope.wait_until_ready()  # wait until the latest streaming values are ready
      self.scope.get_streaming_latest_values(my_streaming_ready)  # get the latest streaming values
      # print(',', end='')
      # print(f'{int(100*self.actual_sample_count/total_samples)} %')

    print()
    print(f'Time spent in aquisition {time.time()-start:1.1f}s')
    print('Waiting for thread ...')
    stream.join()
    sample_process.plot()

    print('Done')
    self.scope.stop()

# if __name__ == '__main__':
#   pymeas = program.PyMeas2019()

#   picoscope = PicoScope()
#   picoscope.connect()
#   for frequency_hz in (1e2, 1e4, 1e6):
#     picoscope.acquire(setup_name='ch1', frequency_hz=frequency_hz, duration_s=5.0, amplitude_Vpp=2.0)