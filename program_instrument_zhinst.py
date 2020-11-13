import time
import logging
import numpy as np

import zhinst
import zhinst.utils
import zhinst.ziPython

import program
import program_measurement_stream

logger = logging.getLogger("logger")

NUM_SAMPLES_PERIOD = 16
SCOPE_INPUT_SELECT = 0  # Signal input 1

# SCOPE_STREAM_RATE: The rate of the scope streaming data, the data will be
# set at a rate of clockbase/2**rate. For example:
#     8  - sets the sampling rate to 7.03 MHz
#     9  - "                         3.50 MHz
#     ...
#     16 - "                         27.5 kHz
SCOPE_STREAM_RATE = 12
DEV = "dev3883"

# pylint: disable=c-extension-no-member


class Instrument:
    def __init__(self, configStep):
        """Perform the operation of opening the instrument connection"""
        self.dev = DEV
        self.clockbase_s = None
        self.rate_s = None
        try:
            # self.log("Descover Zurich Instruments device \"" + self.dev + "\"..")
            discovery = zhinst.ziPython.ziDiscovery()
            self.device_id = discovery.find(self.dev)
            device_props = discovery.get(self.device_id)
            serveraddress = device_props["serveraddress"]
            serverport = device_props["serverport"]
            logger.info(f"Connecting to {self.dev} at {serveraddress}:{serverport}")
            self.daq = zhinst.ziPython.ziDAQServer(serveraddress, serverport, device_props["apilevel"])
        except Exception as e:
            raise Exception(f"Device {self.dev} not found: {e}")

        try:
            _path = f"/{self.dev}/features/devtype"
            _devtype = self.daq.getByte(_path)
            assert _devtype == "MFLI"
        except Exception as e:
            raise Exception(f'Device {self.dev}: Could nt read "{_path}": {e}')

    def warning(self, msg):
        logger.warning(msg)

    def connect(self):
        # ...\zhinst\examples\common\example_autoranging_impedance.py
        """
        Run the example: Connect to a Zurich Instruments Device via the Data Server,
        generate a constant signal on the auxillary outputs and demodulate it in
        order to observe a sine wave in the demodulator X and Y output. Acquire the
        demodulator X and Y output on the scope's streaming channels using subscribe
        and poll (the Scope Module does not support the scopes's streaming
        nodes). Obtains a fixed number of scope samples (defined below as
        num_scope_samples).

        Requirements:

        MF or UHF Instrument with DIG Option (HF2 does not support scope
          streaming).

        Arguments:

        device_id (str): The ID of the device to run the example with. For
          example, `dev2006` or `uhf-dev2006`.

        do_plot (bool, optional): Specify whether to plot the acquired
          data. Default is no plot output. Plotting requires the matplotlib
          module.

        SCOPE_STREAM_RATE: The rate of the scope streaming data, the data will be
        set at a rate of clockbase/2**rate. For example:
          8  - sets the sampling rate to 7.03 MHz
          9  - "             3.50 MHz
          ...
          16 - "             27.5 kHz

        scope_inputselect (list of int, optional): A list containing one or two
          input signals to measure with the scope
          (/dev..../scopes/0/channels/{0,1}/inputselect). For example, [16,
          32]. Example values (see the User Manual for more info):
          0  - signal input 0,
          1  - signal input 1,
          2  - signal output 0,
          3  - signal output 1,
          16 - demod 0 X,
          32 - demod 0 Y.

        Returns:

        data (dict of numpy arrays): The last dictionary as returned by poll.

        scope_samples(list of dict): A list of dictionaries. Each entry in the is
          a dictionary with the keys timestamp and value holding the data obtained
          for one scope channel.

        Raises:

        Exception: If the specified device is not an MF or UHF with the DIG
          Option.

        RuntimeError: If the device is not "discoverable" from the API.

        See the "LabOne Programming Manual" for further help, available:
        - On Windows via the Start-Menu:
          Programs -> Zurich Instruments -> Documentation
        - On Linux in the LabOne .tar.gz archive in the "Documentation"
          sub-folder.
        """
        # Call a zhinst utility function that returns:
        # - an API session `daq` in order to communicate with devices via the data server.
        # - the device ID string that specifies the device branch in the server's node hierarchy.
        # - the device's discovery properties.
        # This example can't run with HF2 Instruments or instruments without the DIG option.

        zhinst.utils.api_server_version_check(self.daq)

        zhinst.utils.disable_everything(self.daq, self.dev)

        self.daq.unsubscribe(f"/{self.dev}/*")

        # Enable the API's log.
        self.daq.setDebugLevel(0)

        # Create a base configuration: Disable all available outputs, awgs, demods, scopes,...
        zhinst.utils.disable_everything(self.daq, self.dev)

        # The value of the instrument's ADC sampling rate.
        self.clockbase_s = self.daq.getInt(f"/{self.dev}/clockbase")
        self.rate_s = self.clockbase_s / 2 ** SCOPE_STREAM_RATE
        logger.info(f"self.clockbase_s: {self.clockbase_s}")
        logger.info(f"self.rate_s: {self.rate_s}")

        # Now configure the instrument for this experiment.
        ####################################################################################################################
        # Configure the scope's channels and streaming nodes.
        # Note: Nodes not listed below not effect the scope streaming data, e.g. (scopes/0/{time,length,trig*,...}).
        ####################################################################################################################
        #
        # 'channels/0/bwlimit' : bandwidth limit the scope data. Enabling bandwidth
        # limiting avoids antialiasing effects due to subsampling when the scope
        # sample rate is less than the input channel's sample rate.
        #  Bool:
        #   0 - do not bandwidth limit
        #   1 - bandwidth limit
        self.daq.setInt(f"/{self.dev}/scopes/0/channels/*/bwlimit", 1)
        # 'channel/0/channels/*/inputselect' : the input channel for the scope:
        #   0 - signal input 1
        #   1 - signal input 2
        #   2, 3 - trigger 1, 2 (front)
        #   8-9 - auxiliary inputs 1-2
        #   The following inputs are additionally available with the DIG option:
        #   10-11 - oscillator phase from demodulator 3-7
        #   16-23 - demodulator 0-7 x value
        #   32-39 - demodulator 0-7 y value
        #   48-55 - demodulator 0-7 R value
        #   64-71 - demodulator 0-7 Phi value
        #   80-83 - pid 0-3 out value
        #   96-97 - boxcar 0-1
        #   112-113 - cartesian arithmetic unit 0-1
        #   128-129 - polar arithmetic unit 0-1
        #   144-147 - pid 0-3 shift value
        # Here, we specify the demod 0 X and y values for channels 1 and 2, respectively.
        self.daq.setInt(f"/{self.dev}/scopes/0/channels/0/inputselect", SCOPE_INPUT_SELECT)
        # 'channels/0/channels/*/limit{lower,upper}
        # Set the scope limits for the data to values far outside legal values
        # allowed by the firmware; the firmware will clamp to the smallest/largest
        # value of the legal lower/upper limits.
        #
        # NOTE: In order to obtain the best possible bit resolution in the scope,
        # these values should be set according to the magnitude of the signals being
        # measured in the scope.
        self.daq.setDouble(f"/{self.dev}/scopes/0/channels/*/limitlower", -10e9)
        self.daq.setDouble(f"/{self.dev}/scopes/0/channels/*/limitupper", 10e9)
        # 'stream/rate' : specifies the rate of the streaming data, the data will be set at a rate of clockbase/2**rate.
        #   7  - sets the samplint rate to 14.06 MHz (maximum rate supported by 1GbE)
        #   8  -              7.03 MHz (maximum rate supported by USB)
        #   9  - "              3.50 MHz
        #   ...
        #   16 - "              27.5 kHz
        self.daq.setDouble(f"/{self.dev}/scopes/0/stream/rate", SCOPE_STREAM_RATE)

        # Perform a global synchronisation between the device and the data server: Ensure that the settings have taken
        # effect on the device before enabling streaming and acquiring data.
        self.daq.sync()

        # Enable the scope streaming nodes:
        self.daq.setInt(f"/{self.dev}/scopes/0/stream/enables/0", 1)

        # Ensure buffers are flushed before subscribing.
        self.daq.sync()

    def acquire(self, configStep, stream_output, com_measurment):  # pylint: disable=too-many-statements,too-many-branches
        assert isinstance(configStep, program.ConfigStep)

        def convert(adu_values):
            return adu_values

        dt_s = 0.0001  # TODO
        stream = program_measurement_stream.InThread(stream_output, dt_s=dt_s, duration_s=configStep.duration_s, func_convert=convert)
        stream.start()

        # Subscribe to the scope's streaming samples in the ziDAQServer session.
        stream_nodepath = f"/{self.dev}/scopes/0/stream/sample"
        self.daq.subscribe(stream_nodepath)

        # We will construct arrays of the scope streaming samples and their timestamps.
        num_scope_samples = int(1e5)  # Critical parameter for memory consumption.
        # Preallocate arrays.
        scope_samples_value = np.nan * np.ones(num_scope_samples)
        scope_samples_timestamp = np.zeros(num_scope_samples, dtype=int)

        n = 0  # The number of scope samples acquired on each channel.
        num_blocks = 0  # Just for statistics.
        poll_count = 0
        timeout = 60
        t_start = time.time()
        while n < num_scope_samples:
            if time.time() - t_start > timeout:
                raise Exception("Failed to acquired %d scope samples after %f s. Num samples acquired")
            data = self.daq.poll(0.02, 200, 0, True)
            poll_count += 1
            if stream_nodepath not in data:
                # Could be the case for very slow streaming rates and fast poll frequencies.
                logger.info("Poll did not return any subscribed data.")
                continue
            num_blocks_poll = len(data[stream_nodepath])
            num_blocks += num_blocks_poll
            logger.info(f"Poll #{poll_count} returned {num_blocks_poll} blocks of streamed scope data. " f"blocks processed {num_blocks} samples acquired {n}.", sep="", end="\r")
            for b, block in enumerate(data[stream_nodepath]):
                flags = block["flags"]
                if flags & 1:
                    self.warning(f"Block {b} from poll indicates dataloss (flags: {flags})")
                    continue
                if flags & 2:
                    # This should not happen.
                    self.warning(f"Block {b} from poll indicates missed trigger (flags: {flags})")
                    continue
                if flags & 3:
                    self.warning(f"Block {b} from poll indicates transfer failure  (flags: {flags})")
                assert block["datatransfermode"] == 3, "The blocks datatransfermode states the block does not contain scope streaming data."
                num_samples_block = len(block["wave"][:, 0])  # The same for all channels.
                if num_samples_block + n > num_scope_samples:
                    num_samples_block = num_scope_samples - n
                ts_delta = int(self.clockbase_s * block["dt"])  # The delta inbetween timestamps.
                assert block["channelenable"][SCOPE_INPUT_SELECT] == 1
                # 'timestamp' is the last sample's timestamp in the block.
                ts_end = block["timestamp"] - (len(block["wave"][:, SCOPE_INPUT_SELECT]) - num_samples_block) * ts_delta
                ts_start = ts_end - num_samples_block * ts_delta
                scope_samples_timestamp[n : n + num_samples_block] = np.arange(ts_start, ts_end, ts_delta)
                scope_samples_value[n : n + num_samples_block] = block["channeloffset"][SCOPE_INPUT_SELECT] + block["channelscaling"][SCOPE_INPUT_SELECT] * block["wave"][:num_samples_block, SCOPE_INPUT_SELECT]

                adu_values = block["channeloffset"][SCOPE_INPUT_SELECT] + block["channelscaling"][SCOPE_INPUT_SELECT] * block["wave"][:num_samples_block, SCOPE_INPUT_SELECT]
                queueFull = stream.put(adu_values)
                if queueFull:
                    stream.put_EOF()
                    logger.info("STOP(queue full)")
                    break

                if com_measurment.requested_stop_soft():
                    stream.put_EOF()
                    logger.info("STOP(ctrl-C pressed)")

                n += num_samples_block

        if com_measurment.requested_stop_soft():
            stream.put_EOF()
            logger.info("STOP(time over)")

        self.daq.sync()
        self.daq.setInt(f"/{self.dev}/scopes/*/stream/enable", 0)
        self.daq.unsubscribe("*")

        logger.info()
        logger.info(f"Total blocks processed {num_blocks}, samples acquired {n}.")

        expected_ts_delta = 2 ** SCOPE_STREAM_RATE

        # Check for sampleloss
        nan_count = np.sum(np.isnan(scope_samples_value))
        zero_count = np.sum(scope_samples_timestamp == 0)
        diff_timestamps = np.diff(scope_samples_timestamp)
        min_ts_delta = np.min(diff_timestamps)
        max_ts_delta = np.max(diff_timestamps)
        if nan_count:
            nan_index = np.where(np.isnan(scope_samples_value))[0]
            self.warning(f"Scope channel {SCOPE_INPUT_SELECT} values contain {int(nan_count)}/{len(scope_samples_value)} nan entries (starting at index {nan_index[0]}).")
        if zero_count:
            self.warning(f"Scope channel {SCOPE_INPUT_SELECT} timestamps contain {int(zero_count)} entries equal to 0.")
        ts_delta_mismatch = False
        if min_ts_delta != expected_ts_delta:
            index = np.where(diff_timestamps == min_ts_delta)[0]
            self.warning(f"Scope channel {SCOPE_INPUT_SELECT} timestamps have a min_diff {min_ts_delta} (first discrepancy at pos: {index[0]}). " f"Expected {expected_ts_delta}.")
            ts_delta_mismatch = True
        if max_ts_delta != expected_ts_delta:
            index = np.where(diff_timestamps == max_ts_delta)[0]
            self.warning(f"Scope channel {SCOPE_INPUT_SELECT} timestamps have a max_diff {max_ts_delta} (first discrepenacy at pos: {index[0]}). " f"Expected {expected_ts_delta}.")
            ts_delta_mismatch = True
        dt = (scope_samples_timestamp[-1] - scope_samples_timestamp[0]) / float(self.clockbase_s)
        logger.info(f"Samples in channel {SCOPE_INPUT_SELECT} span {dt}s at a rate of {self.rate_s/1e3}kHz.")
        assert not nan_count, "Detected NAN in the array of scope samples."
        assert not ts_delta_mismatch, "Detected an unexpected timestamp delta in the scope data."

        return data, scope_samples_timestamp, scope_samples_value

    def close(self):
        self.daq.disconnect()
