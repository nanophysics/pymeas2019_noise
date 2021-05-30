# https://docs.python.org/3/library/multiprocessing.html
import multiprocessing
import os
import time
from multiprocessing import Pool, TimeoutError


class Stage:
    def __init__(self, out):
        self.out = out

    def push(self, x):
        self.out.push(x)

    def done(self):
        self.out.push(None)


class StateTrash:
    def push(self, x):
        print(f"trash {x}")


class QueueOut:
    """
    This is a stream sink and feeds 'queue_out'
    """

    def __init__(self, queue_out):
        self.queue_out = queue_out

    def push(self, x):
        self.queue_out.put(x)

    def done(self):
        self.queue_out.put(None)


class QueueIn:
    """
    Read from the queue 'queue_in' and feed 'out'
    """

    def __init__(self, queue_in, out):
        self.queue_in = queue_in
        self.out = out

    def run(self):
        while True:
            x = self.queue_in.get()
            if x is None:
                self.out.done()
                return 1
            self.out.push(x)


def f_stage_trash(q_in):
    o = StateTrash()
    o = Stage(o)
    qi = QueueIn(queue_in=q_in, out=o)
    return qi.run()


def f_stage(q_in, q_out):
    s = QueueOut(q_out)
    o = Stage(s)
    qi = QueueIn(queue_in=q_in, out=o)
    return qi.run()


def main():
    processes = os.cpu_count() // 2
    with Pool(processes=processes, maxtasksperchild=1) as pool:
        m = multiprocessing.Manager()
        q1 = m.Queue()
        # f_stage_trash(q_in=q1)
        q2 = m.Queue()
        # f_stage(q_in=q2, q_out=q1)
        r1 = pool.apply_async(f_stage_trash, (q1,))
        r2 = pool.apply_async(f_stage, (q2, q1))
        q2.put("r")
        q2.put(None)
        print(r1.get(timeout=1000))
        print(r2.get(timeout=1000))

    # res = pool.apply_async(f, (20,))      # runs in *only* one process
    # print(res.get(timeout=1))             # prints "400"


if __name__ == "__main__":
    main()
