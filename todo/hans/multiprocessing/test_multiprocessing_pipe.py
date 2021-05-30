
# https://docs.python.org/3/library/multiprocessing.html

import time
import multiprocessing as mp
import numpy as np


'''
Lenovo Hans:
CPU: 28%
DONE int16: 242packets, 2420M samples in 10s: 233.3M samples/s
'''

NP_TYPE = np.float32
NP_TYPE = np.int16

ARRAY_SAMPLES = 10000000
SAMPLES_PER_S = 500*1e6
TIME_TOTAL_S = 10.0

def foo(conn):
    start_s = time.time()
    total_samples = 0
    arr = np.zeros(ARRAY_SAMPLES, dtype=NP_TYPE)
    while True:
        conn.send(arr)
        total_samples += len(arr)
        total_s = time.time() - start_s
        should_s = total_samples/SAMPLES_PER_S
        sleep_s = should_s - total_s
        if sleep_s > 0:
            time.sleep(sleep_s)
        if total_s > TIME_TOTAL_S:
            conn.send(None)
            conn.close()
            print("Sender DONE")
            return

def main():
    mp.set_start_method('spawn')
    parent_conn, child_conn = mp.Pipe()
    p = mp.Process(target=foo, args=(child_conn,))
    p.start()
    start_s = time.time()
    total_samples = 0
    total_packets = 0
    while True:
        arr = parent_conn.recv()
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
