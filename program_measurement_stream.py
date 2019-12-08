import queue
import threading

class Stream:
  def __init__(self, dt_s):
    self.list_overflow = []
    self.dt_s = None
    self.queue = queue.Queue()
  

  def worker(self):
    while True:
      volts = self.queue.get()
      if volts is None:
        break
      # start_index, num_samples = item
      # measurementData.fA.write(channel_raw[start_index:start_index+num_samples].tobytes())

  def start(self):
    self.thread = threading.Thread(target=self.worker)
    self.thread.start()

  def put_EOF(self):
    self.queue.put(None)

  def put(self, volts):
    self.queue.put(volts)

  def join(self):
    self.thread.join()
