import re
import os
import time
import logging
import numpy as np
import matplotlib.pyplot as plt
import program

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

import msl.equipment.resources.picotech.picoscope
import msl.equipment

from msl.equipment.resources.picotech.picoscope import callbacks


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
          resolution='14bit' if config.with_channel_D else '16bit',
          # resolution='16bit',  # only used for ps5000a series PicoScope's
          auto_select_power=False,  # for PicoScopes that can be powered by an AC adaptor or by a USB cable
        )
      )
    )

  def connect(self):
    self.scope = self.record.connect()  # establish a connection to the PicoScope

  def acquire(self, config):
    self.scope.set_channel('A', scale=config.input_Vp)
    if config.with_channel_D:
      self.scope.set_channel('D', scale=10.0)
    if False:
      max_sample_rate = 62.5e6
      desired_sample_rate = max_sample_rate/2
      desired_dt_s = 1.0/desired_sample_rate
      desired_buffer_size = 10e6
      desired_sample_time_s = desired_dt_s*desired_buffer_size
    if True:
      max_sample_rate = 6e6
      desired_sample_rate = max_sample_rate/2
      desired_dt_s = 1.0/desired_sample_rate
      desired_sample_time_s = config.duration_s
      desired_buffer_size = desired_sample_time_s//desired_dt_s
    if False:
      max_sample_rate = 2e4
      desired_sample_rate = max_sample_rate/2
      desired_dt_s = 1.0/desired_sample_rate
      desired_sample_time_s = 0.5
      desired_buffer_size = desired_sample_time_s//desired_dt_s
      # StreamingReady Callback: handle=16384, num_samples=932, start_index=0, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=930, start_index=932, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=932, start_index=1862, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=930, start_index=2794, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=932, start_index=3724, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=344, start_index=4656, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=586, start_index=0, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=932, start_index=586, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=930, start_index=1518, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=932, start_index=2448, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=1620, start_index=3380, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=240, start_index=0, overflow=0, trigger_at=0, triggered=1, auto_stop=0, p_parameter=323152552

      # Trigger 0
      # .StreamingReady Callback: handle=16384, num_samples=932, start_index=240, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=930, start_index=1172, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=932, start_index=2102, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=930, start_index=3034, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=932, start_index=3964, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=104, start_index=4896, overflow=0, trigger_at=0, triggered=0, auto_stop=0, p_parameter=323152552
      # .StreamingReady Callback: handle=16384, num_samples=0, start_index=0, overflow=0, trigger_at=0, triggered=0, auto_stop=1, p_parameter=323152552
      # .
      # Writing
      # Done

    # dt, num_samples = self.scope.set_timebase(1e-6, 2.0)  # sample the voltage on Channel A every 1 us, for 100 us
    dt_s, num_samples = self.scope.set_timebase(desired_dt_s, desired_sample_time_s)  # sample the voltage on Channel A every 1 us, for 100 us
    # self.scope.set_sig_gen_builtin_v2(start_frequency=1e6, pk_to_pk=2.0, offset_voltage=0.4)  # create a sine wave
    # Make sure the is no signal before the trigger
    self.scope.set_sig_gen_builtin_v2(start_frequency=config.frequency_Hz, pk_to_pk=config.input_set_Vp, trigger_source='scope_trig', sweeps=0)  # create a sine wave
    # self.scope.set_sig_gen_builtin_v2(start_frequency=1e3, pk_to_pk=2.0, offset_voltage=0.4, trigger_source='scope_trig', shots=100, sweeps=0)  # create a sine wave
    # self.scope.set_sig_gen_builtin_v2(start_frequency=1e3, pk_to_pk=2.0, offset_voltage=0.4, trigger_source='soft_trig', shots=100, sweeps=0)  # create a sine wave
    # self.scope.sig_gen_software_control(1)
    # self.scope.sig_gen_software_control(0)
    self.scope.set_data_buffer('A')
    if config.with_channel_D:
      self.scope.set_data_buffer('D')
    # self.scope.set_trigger('D', 0.0, direction='rising')  # use Channel A as the trigger source at 1V, wait forever for a trigger event
    # self.scope.set_trigger('D', 1.0, timeout=-0.01, direction='raising')  # use Channel A as the trigger source at 1V, wait forever for a trigger event
    # self.scope.set_trigger('A', 1000.0, direction='below')  # use Channel A as the trigger source at 1V, wait forever for a trigger event

    self.streaming_done = False
    self.trigger_at = None

    @callbacks.ps5000aStreamingReady
    def my_streaming_ready(handle, num_samples, start_index, overflow, trigger_at, triggered, auto_stop, p_parameter):
      if False:
        print('StreamingReady Callback: handle={}, num_samples={}, start_index={}, overflow={}, trigger_at={}, '
          'triggered={}, auto_stop={}, p_parameter={}'.format(handle, num_samples, start_index, overflow,
                                  trigger_at, triggered, auto_stop, p_parameter))

      if overflow:
        print('\noverflow')
      if triggered:
        print('\nTrigger {}'.format(trigger_at))
        self.trigger_at=start_index+trigger_at

      print('.', end='')

      if auto_stop:
        print('')
        self.streaming_done = True

    self.scope.set_trigger('A', -1000.0, direction='below', timeout=0.1)
    self.scope.run_streaming(auto_stop=True)
    while not self.streaming_done:
      self.scope.wait_until_ready()  # wait until the latest streaming values are ready
      self.scope.get_streaming_latest_values(my_streaming_ready)  # get the latest streaming values

    channelD_V = None
    if config.with_channel_D:
      channelD_V = self.scope.channel['D'].volts
    measurementData = program.MeasurementData(config)
    measurementData.write(
      channelA = self.scope.channel['A'].volts,
      channelD = channelD_V,
      dt_s = dt_s,
      num_samples = num_samples,
      trigger_at = self.trigger_at,
    )

    print('Done')
    self.scope.stop()

# if __name__ == '__main__':
#   pymeas = program.PyMeas2019()

#   picoscope = PicoScope()
#   picoscope.connect()
#   for frequency_hz in (1e2, 1e4, 1e6):
#     picoscope.acquire(channel_name='ch1', frequency_hz=frequency_hz, duration_s=5.0, amplitude_Vpp=2.0)