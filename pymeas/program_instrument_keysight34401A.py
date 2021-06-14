import sys
import time
import logging

import numpy as np

from . import program_configsetup
from . import program_measurement_stream
from .library_filelock import ExitCode

logger = logging.getLogger("logger")

try:
    import visa
except ImportError as ex:
    logger.error(f"Failed to import ({ex}). Try: pip install vi")
    logger.exception(ex)
    sys.exit(0)


class Instrument:
    def __init__(self, configstep):
        self.streaming_done = False

        self.rm = visa.ResourceManager()
        self.instrument = self.rm.open_resource("GPIB0::12::INSTR")

    def connect(self):
        pass

    def close(self):
        self.instrument.close()

    def acquire(self, configstep, stream_output, filelock_measurement):  # pylint: disable=too-many-statements
        assert isinstance(configstep, program_configsetup.ConfigStep)

        self.instrument.timeout = 50000
        print(self.instrument.write("*RST"))
        print(self.instrument.write("*CLS"))
        # print(self.instrument.write("CONF:VOLT:DC")) # auto range
        print(self.instrument.write(f"CONF:VOLT:DC {configstep.input_Vp.value}"))  # 0.1, 1, 10, 100, 1000
        time.sleep(1.0)
        print(self.instrument.write("TRIG:DEL 0"))  # Trigget delay
        maxmemory = 512
        trig_count = 50
        # assert (trig_count <= maxmemory)
        print(self.instrument.write("TRIG:COUN %d" % trig_count))  # :COUNt {<value>|MINimum|MAXimum|INFinite}  samples pro lesen
        print(self.instrument.write("SAMP:COUN 1"))  # anzahl samples pro lesen  ???
        # produkt aus TRIG:COUN x TRIG:COUN  darf nicht groesser als 512 sein. Anleitung fuer mich sehr unklar.
        print(self.instrument.write("ZERO:AUTO OFF"))  # ZERO:AUTO {OFF|ONCE|ON}
        print(self.instrument.write("INP:IMP:AUTO ON"))
        NPLC = "1"  # NPLC: Integration over powerlinecycles, 0.02 0.2 1 10 100
        # NPLC = '0.2' #NPLC: Integration over powerlinecycles, 0.02 0.2 1 10 100
        print(self.instrument.write("VOLT:DC:NPLC " + NPLC))  # NPLC: Integration over powerlinecycles, 0.02 0.2 1 10 100

        # time.sleep(1.0)

        # print(self.instrument.write("TRIG:SOUR IMM"))
        # time.sleep(1.0)
        # print(self.instrument.write("INIT"))

        time.sleep(0.5)
        print(self.instrument.write("TRIG:SOUR IMM"))
        # time.sleep(0.5)
        # print(self.instrument.write("INIT"))

        dt_s = 0.02 * float(NPLC)
        assert configstep.dt_s == dt_s
        overheadfaktor = 1.0  # 1.14
        total_samples = int(configstep.duration_s / dt_s)

        def convert(values_V):
            return np.array(values_V, dtype=np.float32)

        stream = program_measurement_stream.InThread(stream_output, dt_s=dt_s, duration_s=configstep.duration_s, func_convert=convert)
        stream.start()
        self.streaming_done = False

        def stop(exit_code: ExitCode, reason: str):
            assert isinstance(exit_code, ExitCode)
            assert isinstance(reason, str)
            self.streaming_done = True
            stream.put_EOF(exit_code=exit_code)
            logger.info(f"STOP({reason})")

        start_s = time.time()

        for i in range(total_samples // trig_count):
            values_comma_sep = self.instrument.query("READ?")  # .replace(",", "\n")
            values_V = [configstep.skalierungsfaktor * float(i) for i in values_comma_sep.split(",")]
            queueFull = stream.put(values_V)
            assert not queueFull

            if filelock_measurement.requested_stop_soft():
                stop(ExitCode.CTRL_C, "<ctrl-c> or softstop")
                break

        self.instrument.close()
        stop(ExitCode.OK, "time over")
        self.close()

        logger.info("")
        logger.info(f"Time spent in aquisition {time.time()-start_s:1.1f}s")
        logger.info("Waiting for thread to finish calculations...")
        stream.join()

        logger.info("Done")
