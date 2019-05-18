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
  def __init__(self):
    self.record = msl.equipment.EquipmentRecord(
      manufacturer='Pico Technology',
      model='2204A',
      serial='FU818/554',
      connection=msl.equipment.ConnectionRecord(
        backend=msl.equipment.Backend.MSL,
            address='SDK::ps2000',
            properties={},
      )
    )

  def connect(self):
    self.scope = self.record.connect()  # establish a connection to the PicoScope

  def acquire(self, config):
    self.scope.set_channel('A', scale='10V')  # enable Channel A and set the voltage range to be +/-10V
    self.scope.set_channel('B', scale='10V')  # enable Channel A and set the voltage range to be +/-10V
    # max_sample_rate = 62.5e6
    max_sample_rate = 10e3
    desired_sample_rate = max_sample_rate/2
    desired_dt_s = 1.0/desired_sample_rate
    desired_buffer_size = 10e6
    desired_sample_time_s = desired_dt_s*desired_buffer_size

    desired_sample_time_s= 150*desired_dt_s
    dt_s, num_samples = self.scope.set_timebase(desired_dt_s, desired_sample_time_s)  # sample the voltage on Channel A every 1 us, for 100 us
    # self.scope.set_sig_gen_builtin_v2(start_frequency=config.frequency_Hz, pk_to_pk=config.input_set_Vp, offset_voltage=0.4, trigger_source='scope_trig', sweeps=0)  # create a sine wave
    # self.scope.set_data_buffer('A')  # set the data buffer for Channel A
    # self.scope.set_data_buffer('D')  # set the data buffer for Channel A

    # no_of_samples = 150
    # duration = 0.4
    # computed_timebase = duration / no_of_samples
    # max_timebase_requested = computed_timebase / 4

              # we manually invoke the Library method, to check that if invalid options sneak through, we throw
              # a different error:
              # desired_sample_time_s= 150*desired_dt_s
              # self.scope.set_timebase(dt=desired_dt_s, duration=desired_sample_time_s, segment_index=0, oversample=0)

              # FASTEST_TIMEBASE = 1
              # timebase_info = self.scope.get_timebase(timebase=FASTEST_TIMEBASE, no_of_samples=150, oversample=0)
              # # time_interval.value*1e-9, max_samples.value, time_units.value
              # time_interval_choosen, max_samples, time_unit = timebase_info


    streaming_done = False

    @callbacks.GetOverviewBuffersMaxMin
    def my_get_overview_buffer(overviewBuffers, overflow, triggeredAt, triggered, auto_stop, nValues):
        print('StreamingReady Callback: overviewBuffers={}, overflow={}, auto_stop={}, nValues={}'.format(overviewBuffers, overflow, auto_stop, nValues))
        global streaming_done
        streaming_done = bool(auto_stop)

    self.scope.run_streaming()  # start streaming mode
    while not streaming_done:
        self.scope.wait_until_ready()  # wait until the latest streaming values are ready
        self.scope.get_streaming_latst_value(my_get_overview_buffer)  # get the latest streaming values

    measurementData = program.MeasurementData(config)
    measurementData.write(
      channelA = self.scope.channel['A'].volts,
      channelD = self.scope.channel['D'].volts,
      dt_s = dt_s,
      num_samples = num_samples,
      trigger_at = self.trigger_at,
    )

    print('Done')
    self.scope.stop()

if __name__ == '__main__':
    picoscope = PicoScope()
    picoscope.connect()

    import program
    config = program.Configuration()
    config.duration_s = 2.0
    config.frequency_Hz = 1000.0
    config.input_set_Vp = 1.0
    config.input_Vp = 1.0
    config.skalierungsfaktor = 1.0
    config.diagram_legend = 'Test'
    config.channel_name = 'Channel X'
    picoscope.acquire(config)
#   pymeas = program.PyMeas2019()

#   picoscope = PicoScope()
#   picoscope.connect()
#   for frequency_hz in (1e2, 1e4, 1e6):
#     picoscope.acquire(channel_name='ch1', frequency_hz=frequency_hz, duration_s=5.0, amplitude_Vpp=2.0)