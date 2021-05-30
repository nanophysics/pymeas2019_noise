
# https://docs.python.org/3/library/multiprocessing.html

import time
import multiprocessing as mp
import numpy as np


'''
Lenovo Hans:
Analog measurement-actual\run_measure_synthetic.py:
CPU: 2.0%
DONE float32: 25packets, 52M samples in 11s: 4.7M samples/s

CPU: 1.5%
DONE int16: 101packets, 101M samples in 10s: 9.7M samples/s

CPU: 4%
DONE int16: 501packets, 501M samples in 10s: 48.3M samples/s

CPU: 25%
DONE int16: 2001packets, 2001M samples in 10s: 193.4M samples/s

CPU: 25%
DONE int16: 5001packets, 5001M samples in 21s: 237.7M samples/s

CPU: 28%
DONE int16: 501packets, 5010M samples in 22s: 226.2M samples/s
'''

NP_TYPE = np.float32
# NP_TYPE = np.int16

ARRAY_SAMPLES = 2097152
SAMPLES_PER_S = 39062500/8
TIME_TOTAL_S = 10.0

def foo(queue):
    start_s = time.time()
    total_samples = 0
    arr = np.zeros(ARRAY_SAMPLES, dtype=NP_TYPE)
    while True:
        queue.put(arr)
        total_samples += len(arr)
        total_s = time.time() - start_s
        should_s = total_samples/SAMPLES_PER_S
        sleep_s = should_s - total_s
        if sleep_s > 0:
            time.sleep(sleep_s)
        if total_s > TIME_TOTAL_S:
            queue.put(None)
            print("Sender DONE")
            return

def main():
    mp.set_start_method('spawn')
    queue = mp.Queue()
    p = mp.Process(target=foo, args=(queue,))
    p.start()
    start_s = time.time()
    total_samples = 0
    total_packets = 0
    while True:
        arr = queue.get()
        if arr is None:
            duration_s = time.time() - start_s
            print(f"DONE {NP_TYPE.__name__}: {total_packets}packets, {total_samples//1000000}M samples in {duration_s:0.0f}s: {total_samples/1000000/duration_s:0.1f}M samples/s")
            break
        total_packets += 1
        total_samples += len(arr)
        # print(f"len={len(arr)}")
    p.join()

if __name__ == '__main__':
    main()
