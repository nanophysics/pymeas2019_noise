import itertools
import numpy as np
import program_eseries

class Classify:
  def __init__(self, series='E12', minimal=1e-9, maximal=1e2):
    self.eseries = program_eseries.eseries(series=series, minimal=minimal, maximal=maximal, borders=True)
    # Take all right borders
    borders = [x[2] for x in self.eseries]
    # Take the rightmost border away
    borders = borders[:-1]
    self.__borders = np.array(borders, dtype=float)
    self.V = [x[1] for x in self.eseries]

  @property
  def bin_count(self):
    return len(self.__borders)+1

  def find_bin_index(self, value):
    return self.__borders.searchsorted(value)

  def bins_factory(self):
    return ClassifyBins(self)

class ClassifyBins:
  def __init__(self, classify):
    assert isinstance(classify, Classify)
    self.classify = classify
    self.count = np.zeros(classify.bin_count, dtype=np.int32)

  def add(self, value):
    idx = self.classify.find_bin_index(value)
    self.count[idx] += 1

  @property
  def V(self):
    return self.classify.V

def test():
  classify = Classify()
  count = classify.bins_factory()

  def timeit_intersect():
    l = (
      (1e-12, 0),
      (1e-4, 61),
      (1e-5, 49),
      (1e2, 133)
    )
    for v, expected_idx in l:
      count.add(v)
      
  timeit_intersect()

  print('V, count')
  print(classify.V)
  print(count.count)
  print(f'V={len(classify.V)}, count={len(count.count)}')

# def test_timeit():
#   classify = Classify()
#   count = classify.bins_factory()

#   def timeit_intersect():
#     l = (
#       (1e-12, 0),
#       (1e-4, 61),
#       (1e-5, 49),
#       (1e2, 133)
#     )
#     for v, expected_idx in l:
#       count.add(v)

#   import timeit
#   print(timeit.timeit('timeit_intersect()', globals=globals(), number=100000))

def test_numpy_searchsorted():
  '''
  >>> 5
  5
  >>> x = np.array([1, 2, 4])
  >>> x.searchsorted(0.8)
  0
  >>> x.searchsorted(1.5)
  1
  >>> x.searchsorted(4.1)
  3
  '''
  pass

def test_diff():
  '''
  >>> 5
  5
  >>> x = np.array([1, 2, 4, 7, 0])
  >>> np.diff(x)
  array([ 1,  2,  3, -7])
  >>> np.abs(np.diff(x))
  array([1, 2, 3, 7])
  '''
  pass

if __name__ == '__main__':
  if True:
    import doctest
    doctest.testmod()
  
  test()
  # test_timeit()
  

