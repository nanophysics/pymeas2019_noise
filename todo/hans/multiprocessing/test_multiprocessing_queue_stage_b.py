
# https://docs.python.org/3/library/multiprocessing.html

import time
import multiprocessing as mp

# Cant pickle weakref objects

class Stage:
    def __init__(self, out):
        self.out = out
        self.queue = mp.Queue()
        self.p = mp.Process(target=self.run)
        self.p.start()

    def run(self):
        print('Muh')
        while True:
            x = self.queue.get()
            self.out.push(f'{x}-{x}')

    def push(self, x):
        self.queue.put(x)

class StateTrash:
    def push(self, x):
        print(x)

def main():
    o = StateTrash()
    o = Stage(o)
    o = Stage(o)
    o.push('r')

if __name__ == '__main__':
    main()
