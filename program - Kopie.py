

import os
import time
import logging
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

import msl.equipment.resources.picotech.picoscope
import msl.equipment

from msl.equipment.resources.picotech.picoscope import callbacks

directory = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':

    print('Example :: Streaming Mode')

    record = msl.equipment.EquipmentRecord(
        manufacturer='Pico Technology',
        model='5442D',
        # serial='GQ903/0003',
        connection=msl.equipment.ConnectionRecord(
            backend=msl.equipment.Backend.MSL,
            address='SDK::ps5000a',
            # properties={'open_async': True},  # opening in async mode is done in the properties
            properties=dict(
                resolution='14bit',  # only used for ps5000a series PicoScope's
                # resolution='16bit',  # only used for ps5000a series PicoScope's
                auto_select_power=False,  # for PicoScopes that can be powered by an AC adaptor or by a USB cable
            )
        )
    )

    streaming_done = False
    global_trigger_at = None

    @callbacks.ps5000aStreamingReady
    def my_streaming_ready(handle, num_samples, start_index, overflow, trigger_at, triggered, auto_stop, p_parameter):
        if False:
            print('StreamingReady Callback: handle={}, num_samples={}, start_index={}, overflow={}, trigger_at={}, '
                'triggered={}, auto_stop={}, p_parameter={}'.format(handle, num_samples, start_index, overflow,
                                                                trigger_at, triggered, auto_stop, p_parameter))

        if overflow:
            print('\noverflow')
        if triggered:
            print('\nTrigger{}'.format(trigger_at))
            global global_trigger_at
            global_trigger_at=trigger_at

        print('.', end='')

        if auto_stop:
            print('')
            global streaming_done
            streaming_done = True

    scope = record.connect()  # establish a connection to the PicoScope
    scope.set_channel('A', scale='10V')  # enable Channel A and set the voltage range to be +/-10V
    scope.set_channel('D', scale='10V')  # enable Channel A and set the voltage range to be +/-10V
    max_sample_rate = 62.5e6
    desired_sample_rate = max_sample_rate/2
    desired_dt_s = 1.0/desired_sample_rate
    desired_buffer_size = 10e6
    desired_sample_time_s = desired_dt_s*desired_buffer_size
    # dt, num_samples = scope.set_timebase(1e-6, 2.0)  # sample the voltage on Channel A every 1 us, for 100 us
    dt_s, num_samples = scope.set_timebase(desired_dt_s, desired_sample_time_s)  # sample the voltage on Channel A every 1 us, for 100 us
    # scope.set_sig_gen_builtin_v2(start_frequency=1e6, pk_to_pk=2.0, offset_voltage=0.4)  # create a sine wave
    scope.set_sig_gen_builtin_v2(start_frequency=1e3, pk_to_pk=2.0, offset_voltage=0.4, trigger_source='scope_trig', sweeps=0)  # create a sine wave
    # scope.set_sig_gen_builtin_v2(start_frequency=1e3, pk_to_pk=2.0, offset_voltage=0.4, trigger_source='scope_trig', shots=100, sweeps=0)  # create a sine wave
    # scope.set_sig_gen_builtin_v2(start_frequency=1e3, pk_to_pk=2.0, offset_voltage=0.4, trigger_source='soft_trig', shots=100, sweeps=0)  # create a sine wave
    # scope.sig_gen_software_control(1)
    # scope.sig_gen_software_control(0)
    scope.set_data_buffer('A')  # set the data buffer for Channel A
    scope.set_data_buffer('D')  # set the data buffer for Channel A
    # scope.set_trigger('D', 0.0, direction='rising')  # use Channel A as the trigger source at 1V, wait forever for a trigger event
    # scope.set_trigger('D', 1.0, timeout=-0.01, direction='raising')  # use Channel A as the trigger source at 1V, wait forever for a trigger event
    # scope.set_trigger('A', 1000.0, direction='below')  # use Channel A as the trigger source at 1V, wait forever for a trigger event
    scope.set_trigger('A', -1000.0, direction='below', timeout=0.2)  # use Channel A as the trigger source at 1V, wait forever for a trigger event
    scope.run_streaming(auto_stop=True)  # start streaming mode
    while not streaming_done:
        scope.wait_until_ready()  # wait until the latest streaming values are ready
        scope.get_streaming_latest_values(my_streaming_ready)  # get the latest streaming values

    aux_data = dict(
        dt_s = dt_s,
        num_samples = num_samples,
        global_trigger_at = global_trigger_at,
    )
    filename = os.path.join(directory, 'data.npz')
    print('Writing ' + filename)
    np.savez(filename, scope.channel['A'].volts, scope.channel['D'].volts)
    with open(os.path.join(directory, 'data.aux'), 'w') as f:
        f.write(str(aux_data))

    print('Stopping the PicoScope')
    scope.stop()