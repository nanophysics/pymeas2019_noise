# https://docs.python.org/3/library/multiprocessing.html
import multiprocessing
import os
import logging

logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.DEBUG)

class Stage:
    def __init__(self, out):
        self.out = out

    def push(self, x):
        self.out.push(f"x:{x}")

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


class ProcessPool:
    def __init__(self, pool):
        self.pool = pool
        self.manager = multiprocessing.Manager()
        self.q = self.manager.Queue()
        self.r = []

    def sink(self, f):
        r = self.pool.apply_async(f, (self.q,))
        self.r.append(r)

    def append(self, f):
        q_in = self.manager.Queue()
        r = self.pool.apply_async(f, (q_in, self.q))
        self.q = q_in
        self.r.append(r)

    def join(self):
        for r in self.r:
            print(r.get(timeout=1000))


def main():
    processes = os.cpu_count() // 2
    with multiprocessing.Pool(processes=processes, maxtasksperchild=1) as pool:
        pp = ProcessPool(pool)
        pp.sink(f_stage_trash)
        pp.append(f_stage)
        pp.append(f_stage)
        pp.q.put("r")
        pp.q.put(None)
        pp.join()


if __name__ == "__main__":
    main()
