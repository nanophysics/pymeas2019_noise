import sys
import queue
import threading

is64bit = sys.maxsize > 2**32
if is64bit:
  SIZE_MAX_BYTES = 1e9
else:
  SIZE_MAX_BYTES = 1e8
BYTES_FLOAT = 8
SIZE_MAX_FLOATS = SIZE_MAX_BYTES//BYTES_FLOAT

class Stream:
  def __init__(self, out, dt_s):
    self.out = out
    self.dt_s = dt_s
    self.list_overflow = []
    self.queue = queue.Queue()
    self.queue_size = 0
    self.out.init(stage=0, dt_s=dt_s)

  def worker(self):
    while True:
      array_in = self.queue.get()
      if array_in is None:
        self.out.flush()
        break
      self.queue_size -= len(array_in)
      assert self.queue_size >= 0
      self.out.push(array_in)

  def start(self):
    self.thread = threading.Thread(target=self.worker)
    self.thread.start()

  def put_EOF(self):
    self.queue.put(None)

  def put(self, volts):
    self.queue.put(volts)
    assert self.queue_size >= 0
    self.queue_size += len(volts)
    # Return True if queue is full
    return self.queue_size > SIZE_MAX_FLOATS

  def join(self):
    self.thread.join()

if __name__ == '__main__':
  if True:
    import numpy as np
    import program_fir
    sp = program_fir.SampleProcess(fir_count=3)
    i = Stream(sp.output, dt_s=0.01)
    i.start()

    if True:
      time_total_s = 10.0
      t = np.arange(0, time_total_s, i.dt_s)
      #nse = np.random.randn(len(t))
      r = np.exp(-t / 0.05)
      #cnse = np.convolve(nse, r) * dt_s
      #cnse = cnse[:len(t)]
      s = 1.0 * np.sin(2 * np.pi * t / 2.0) #+ 0 * cnse

      i.put(s)
      i.put_EOF()

    i.join()
    sp.plot()

  if False:
    import program_fir

    sp = program_fir.SampleProcess(fir_count=3)
    i = program_fir.InSin(sp.output, time_total_s=10.0, dt_s=0.01)
    i.process()
    sp.plot()

