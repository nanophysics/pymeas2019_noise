from scipy import signal
import matplotlib.pyplot as plt
import numpy as np

offset = 100.0

fs = 10e3
N = 1e5
amp = 2*np.sqrt(2)
amp = 0.0
freq = 1234.0
noise_power = 0.001 * fs / 2
noise_power = 1e-10 * noise_power
time = np.arange(N) / fs
x = amp*np.sin(2*np.pi*freq*time)
x += np.random.normal(scale=np.sqrt(noise_power), size=time.shape)
x += offset
x += np.linspace(0.0, 10.0, N)

#f, Pxx_den = signal.periodogram(x, fs, detrend='linear')
#f, Pxx_den = signal.periodogram(x, fs, detrend='constant')
#f, Pxx_den = signal.periodogram(x, fs, detrend=None)
#f, Pxx_den = signal.periodogram(x, fs, window='hamming')
f, Pxx_den = signal.periodogram(x, fs, window='hamming',detrend='linear')
plt.semilogy(f, Pxx_den)
plt.xlabel('frequency [Hz]')
plt.ylabel('PSD [V**2/Hz]')
plt.show()
