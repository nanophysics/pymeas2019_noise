
# https://docs.python.org/3/library/multiprocessing.html
# https://medium.com/analytics-vidhya/using-numpy-efficiently-between-processes-1bee17dcb01

import time
import ctypes
import multiprocessing as mp
import numpy as np


'''
Lenovo Hans:
CPU: 0%
DONE float32: 501packets, 50100M samples in 10s: 4916.8M samples/s
'''

NP_TYPE = np.int16
NP_TYPE = np.float32

ARRAY_SAMPLES = 100*1000*1000
SHM_SAMPLES = 10*ARRAY_SAMPLES
SAMPLES_PER_S = 5*1e9
TIME_TOTAL_S = 10.0

def foo(queue, np_arr_shape, mp_array, np_array):
    start_s = time.time()
    total_samples = 0
    total_packets = 0
    while True:
        # Prepare and send one packet
        # mp_array.acquire()
        np_array[0] = total_packets
        total_samples += ARRAY_SAMPLES
        total_packets += 1
        queue.put(total_samples)

        # Wait till the picoscope has more data.
        total_s = time.time() - start_s
        should_s = total_samples/SAMPLES_PER_S
        sleep_s = should_s - total_s
        if sleep_s > 0:
            time.sleep(sleep_s)

        # Done
        if total_s > TIME_TOTAL_S:
            queue.put(None)
            print("Sender DONE")
            return

def main():
    mp.set_start_method('spawn')
    queue = mp.Queue()

    np_arr_shape = (ARRAY_SAMPLES,)
    mp_array = mp.Array(ctypes.c_float, ARRAY_SAMPLES, lock=mp.Lock())
    # create a numpy view of the array
    np_array = np.frombuffer(mp_array.get_obj(), dtype=ctypes.c_float).reshape(np_arr_shape)
    p = mp.Process(target=foo, args=(queue, np_arr_shape, mp_array, np_array))
    p.start()

    start_s = time.time()
    total_samples_tail = 0
    total_packets = 0
    total_samples = 0
    while True:
        token = queue.get()
        # mp_array.release()
        if token is None:
            duration_s = time.time() - start_s
            print(f"DONE {NP_TYPE.__name__}: {total_packets}packets, {total_samples//1000000}M samples in {duration_s:0.0f}s: {total_samples/1000000/duration_s:0.1f}M samples/s")
            break
        total_samples = token
        total_packets += 1
        assert total_samples-total_samples_tail == ARRAY_SAMPLES, "too slow in reading data"
        total_samples_tail = total_samples
    p.join()

if __name__ == '__main__':
    main()
