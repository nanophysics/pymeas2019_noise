
# https://docs.python.org/3/library/multiprocessing.html

import time
import multiprocessing as mp


class Stage:
    def __init__(self, out):
        self.out = out

    def push(self, x):
        self.out.push(f'{x}-{x}')

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
