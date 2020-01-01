import math
import time
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt

gain = 1.0 #1.0e-3
x = gain * np.loadtxt(fname = "file_1M_1e-3_labview.txt")[:,1]
print (x)
dt_s = 1.0e-3 # 8.0e-7
f, power = scipy.signal.periodogram(x, 1.0/dt_s, window='hamming',) #Hz, V^2/Hz
density = np.sqrt(power)

print (np.sqrt (np.mean(power[:100])))


plt.loglog(f, density)
plt.ylim( 1e-8,1e-6)
plt.xlim(1e2, 1e5)
plt.grid(True)
plt.show() 