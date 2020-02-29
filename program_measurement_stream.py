import sys
import time
import queue
import threading

is64bit = sys.maxsize > 2**32
if is64bit:
  SIZE_MAX_BYTES = 1e9
else:
  SIZE_MAX_BYTES = 1e9
BYTES_INT16 = 2
SIZE_MAX_INT16 = SIZE_MAX_BYTES//BYTES_INT16

class Progress:
  def __init__(self, dt_s, duration_s):
    self.__dt_s = dt_s
    self.__duration_s = duration_s
    self.__start_s = time.time()
    self.__print_update_interval_s = 10.0
    self.__next_update_s = self.__start_s + 2*self.__print_update_interval_s
  
  def tick(self, samples):
    now_s = time.time()
    if now_s < self.__next_update_s:
      return
    self.__next_update_s += self.__print_update_interval_s
    spent_s = now_s-self.__start_s
    remaining_s = max(0.0, self.__duration_s - spent_s)

    str_spent_s = self.__time(spent_s)
    str_remaining_s = self.__time(remaining_s)
    str_samples = f'{samples:,d}'.replace(',','\'')
    msg = f'Spent: {str_spent_s}, remaining_s: {str_remaining_s}, collected samples {str_samples}, type Ctrl-C to abort'
    print(msg)

  def __time(self, s):
    s = int(s)
    seconds = s % 60
    s = s // 60
    minutes = s % 60
    s = s // 60
    hours = s % 24
    s = s // 24
    days = s
    return f'{days:d}d {hours:2d}h {minutes:2d}m {seconds:2d}s'

class InThread:
  '''
  A Stream Source.
  Given `out`: Stream-Interface to push to.
  Given `dt_s`: The sampling interval.

  Another thread may push into the stream:
    put(volts)
    put_EOF()

  The worker thread of the stream
  '''
  def __init__(self, out, dt_s, func_convert, duration_s=None):
    self.out = out
    self.dt_s = dt_s
    self.__func_convert = func_convert
    self.list_overflow = []
    self.__samples_processed = 0
    self.__queue = queue.Queue()
    self.__queue_size = 0
    self.__queue_size_max = SIZE_MAX_INT16/50 # 2%
    self.out.init(stage=0, dt_s=dt_s)
    self.__progress = Progress(dt_s, duration_s)
    self.__lock = threading.Lock()

  def worker(self):
    while True:
      raw_data_in = self.__queue.get()
      if raw_data_in is None:
        self.out.done()
        break
      samples = len(raw_data_in)
      with self.__lock:
        self.__queue_size -= samples
      assert self.__queue_size >= 0
      self.__samples_processed += samples
      # print('push: ', end='')
      array_in = self.__func_convert(raw_data_in)
      rc = self.out.push(array_in)
      self.__progress.tick(self.__samples_processed)
      assert rc is None
  
  def start(self):
    self.thread = threading.Thread(target=self.worker)
    self.thread.start()

  def put_EOF(self):
    self.__queue.put(None)

  def put(self, raw_data):
    self.__queue.put(raw_data)
    assert self.__queue_size >= 0
    samples = len(raw_data)
    with self.__lock:
      self.__queue_size += samples
    if self.__queue_size > self.__queue_size_max:
      self.__queue_size_max = min(int(1.5*self.__queue_size), SIZE_MAX_INT16)
      print(f'Max queue size: used {100.0*self.__queue_size/SIZE_MAX_INT16:.0f}%')
    # Return True if queue is full
    return self.__queue_size > SIZE_MAX_INT16

  def join(self):
    self.thread.join()

if __name__ == '__main__':
  if True:
    import numpy as np
    import program_fir
    sp = program_fir.SampleProcess(fir_count=3)
    i = InThread(sp.output, dt_s=0.01)
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

