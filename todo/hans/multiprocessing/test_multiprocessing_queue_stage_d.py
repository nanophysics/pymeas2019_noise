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


class ProcessQueue:
    def __init__(self, out):
        self.queue = multiprocessing.Queue()
        self.out = out


def f_stage_trash(q_in):
    print("f_stage_trash", flush=True)
    o = StateTrash()
    o = Stage(o)
    while True:
        x = q_in.get()
        if x is None:
            print("f_stage_trash done", flush=True)
            o.done()
            return 1
        print(f"f_stage_trash {x}", flush=True)
        o.push(x)


def f_stage(q_in, q_out):
    print("f_stage", flush=True)

    class Sink:
        def __init__(self, q_out):
            self.q_out = q_out

        def push(self, x):
            self.q_out.put(x)

        def done(self):
            self.q_out.put(None)

    s = Sink(q_out)
    o = Stage(s)
    while True:
        x = q_in.get()
        if x is None:
            print("f_stage done", flush=True)
            o.done()
            return 2
        print(f"f_stage {x}", flush=True)
        o.push(x)


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
