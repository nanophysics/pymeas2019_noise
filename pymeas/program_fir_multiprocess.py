import sys
from enum import Enum

import multiprocessing as mp


class Func(Enum):
    PUSH = 0
    PRINT_SIZE = 1
    DONE = 2

def run(queue, out):
    while True:
        func, arg = queue.get()
        if func == Func.PUSH:
            out.push(array_in=arg)
            continue

        if func == Func.PRINT_SIZE:
            out.print_size(f=sys.stdout)
            continue

        if func == Func.DONE:
            out.done()
            return

        raise NotImplementedError()

class InterprocessQueue:
    """
    Stream-Sink: Implements a Stream-Interface
    """
    def __init__(self, out):
        self.out = out
        self.prev = None
        self.stage = None
        self.dt_s = None
        self.queue = mp.Queue()
        self.process = mp.Process(target=run, args=(self.queue, self.out))

    def init(self, stage, dt_s, prev):
        self.prev = prev
        self.stage = stage
        self.dt_s = dt_s
        self.out.init(stage=stage, dt_s=dt_s, prev=self)
        self.process.start()

    def done(self):
        return
        self.queue.put((Func.DONE, None))

    def print_size(self, f):
        return
        self.queue.put((Func.PRINT_SIZE, None))

    def push(self, array_in):
        return
        self.queue.put((Func.PUSH, array_in))
