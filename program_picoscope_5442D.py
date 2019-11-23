import re
import os
import time
import queue
import logging
import numpy as np
import threading
import matplotlib.pyplot as plt
import program

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

  def acquire(self, configSetup):
    assert isinstance(configSetup, program.ConfigSetup)

    assert type(configSetup.input_Vp) == self.scope.enRange

    self.scope.set_channel('A', coupling='dc', scale=configSetup.input_Vp)

    max_samples_bytes = self.scope.memory_segments(num_segments=1)
    desired_buffer_size = max_samples_bytes//1  # 1 channels

    max_sampling_rate = 250e6
    while True:
      desired_sample_rate = max_sampling_rate//2
      desired_dt_s = 1.0/desired_sample_rate
      desired_sample_time_s = desired_buffer_size*desired_dt_s
      total_samples = int(configSetup.duration_s/desired_dt_s)
      assert total_samples > 1000

      max_filesize = configSetup.max_filesize_bytes
      max_samples = max_filesize // 2  # 2 bytes/sample
      if total_samples <= max_samples*1.001:
        break

      reduction = max_samples/total_samples
      max_sampling_rate_before = max_sampling_rate
      max_sampling_rate *= reduction
      print(f'Reducing sample rate by {reduction}. {max_sampling_rate_before:.4e} -> {max_sampling_rate:.4e}')

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

    dt_s, num_samples = self.scope.set_timebase(desired_dt_s, desired_sample_time_s)  # sample the voltage on Channel A every 1 us, for 100 us
    print(f'set_timebase({desired_dt_s:.4e}) -> {dt_s:.4e}')
    print(f'configSetup.duration_s={configSetup.duration_s:.4e}, total_samples*dt_s={total_samples*dt_s:.4e}')

    self.scope.set_data_buffer('A')
    channelA_raw = self.scope.channel['A'].raw

    # logfile = configMeasurement.get_logfile()
    measurementData = program.MeasurementData(configSetup)
    measurementData.open_files('wb')

    self.queue = queue.Queue()

    def worker():
      while True:
        item = self.queue.get()
        if item is None:
          break
        start_index, num_samples = item
        measurementData.fA.write(channelA_raw[start_index:start_index+num_samples].tobytes())

    thread = threading.Thread(target=worker)
    thread.start()

    self.actual_sample_count = 0
    self.streaming_done = False

    @callbacks.ps5000aStreamingReady
    def my_streaming_ready(handle, num_samples, start_index, overflow, trigger_at, triggered, auto_stop, p_parameter):
      if False:
        print('StreamingReady Callback: handle={}, num_samples={}, start_index={}, overflow={}, trigger_at={}, '
          'triggered={}, auto_stop={}, p_parameter={}'.format(handle, num_samples, start_index, overflow,
                                  trigger_at, triggered, auto_stop, p_parameter))

      self.queue.put((start_index, num_samples))

      if overflow:
        # logfile.write(f'Overflow: {self.actual_sample_count+start_index}\n')
        measurementData.list_overflow.append(self.actual_sample_count+start_index)

      self.actual_sample_count += num_samples
      if self.actual_sample_count > total_samples:
        self.streaming_done = True
        self.queue.put(None)

      if overflow:
        print('\noverflow')
      print('.', end='')

      assert auto_stop == False
      assert triggered == False

    self.scope.run_streaming(auto_stop=False)
    while not self.streaming_done:
      self.scope.wait_until_ready()  # wait until the latest streaming values are ready
      self.scope.get_streaming_latest_values(my_streaming_ready)  # get the latest streaming values


    print(f'Waiting for thread ...')
    thread.join()

    measurementData.close_files()
    measurementData.channelA_volts_per_adu = self.scope.channel['A'].volts_per_adu
    measurementData.dt_s = dt_s
    measurementData.num_samples = self.actual_sample_count
    measurementData.write()
    # logfile.close()

    print('Done')
    self.scope.stop()

# if __name__ == '__main__':
#   pymeas = program.PyMeas2019()

#   picoscope = PicoScope()
#   picoscope.connect()
#   for frequency_hz in (1e2, 1e4, 1e6):
#     picoscope.acquire(setup_name='ch1', frequency_hz=frequency_hz, duration_s=5.0, amplitude_Vpp=2.0)