import sys
import queue
import threading

is64bit = sys.maxsize > 2**32
if is64bit:
  SIZE_MAX_BYTES = 1e9
else:
  SIZE_MAX_BYTES = 1e8
BYTES_INT16 = 2
SIZE_MAX_INT16 = SIZE_MAX_BYTES//BYTES_INT16


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
  def __init__(self, out, dt_s, func_convert):
    self.out = out
    self.dt_s = dt_s
    self.__func_convert = func_convert
    self.list_overflow = []
    self.queue = queue.Queue()
    self.queue_size = 0
    self.queue_size_max = SIZE_MAX_INT16/50 # 2%
    self.out.init(stage=0, dt_s=dt_s)

  def worker(self):
    while True:
      raw_data_in = self.queue.get()
      if raw_data_in is None:
        self.out.done()
        break
      self.queue_size -= len(raw_data_in)
      assert self.queue_size >= 0
      # print('push: ', end='')
      array_in = self.__func_convert(raw_data_in)
      rc = self.out.push(array_in)
      assert rc is None

      # while True:
      #   calculation_stage = self.out.push(None)
      #   assert isinstance(calculation_stage, str)
      #   done = len(calculation_stage) == 0
      #   if done:
      #     break

  def worker_obsolete(self):
    block = True
    push_count = 0
    # push_count_max = 3
    while True:
      try:
        raw_data_in = self.queue.get(block=block)
        block = False
      except queue.Empty:
        assert block == False
        calculation_stage = self.out.push(None)
        push_count += 1
        assert isinstance(calculation_stage, str)
        block = len(calculation_stage) == 0
        push_count += 1
        # if block:
        #   if push_count_max < push_count:
        #     push_count_max = push_count
        #     print(f'Push count {push_count}')
        #   push_count = 0
        continue
      if raw_data_in is None:
        break
      if (not block) and (push_count > 0):
        print(f'Could not finish calculating after push_count {push_count}!')
      push_count = 0
      self.queue_size -= len(raw_data_in)
      assert self.queue_size >= 0
      # print('push: ', end='')
      array_in = self.__func_convert(raw_data_in)
      rc = self.out.push(array_in)
      assert rc is None

  def start(self):
    self.thread = threading.Thread(target=self.worker)
    self.thread.start()

  def put_EOF(self):
    self.queue.put(None)

  def put(self, raw_data):
    self.queue.put(raw_data)
    assert self.queue_size >= 0
    self.queue_size += len(raw_data)
    if self.queue_size > self.queue_size_max:
      self.queue_size_max = min(int(1.5*self.queue_size), SIZE_MAX_INT16)
      print(f'Max queue size: used {100.0*self.queue_size/SIZE_MAX_INT16:.0f}%')
    # Return True if queue is full
    return self.queue_size > SIZE_MAX_INT16

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

  if False:
    import program_fir

    sp = program_fir.SampleProcess(fir_count=3)
    i = program_fir.InSin(sp.output, time_total_s=10.0, dt_s=0.01)
    i.process()
    sp.plot()

