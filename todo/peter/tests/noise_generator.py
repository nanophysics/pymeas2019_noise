from scipy import signal
import matplotlib.pyplot as plt
import numpy as np

dt_s = 0.001

def process(sample_start, samples, dt_s, sine_amp_V_rms = 0.1, noise_density_V_sqrtHz = 0.1):
    # test signal to test the algorythm
    # produces sines every decade with added white noise
    # you should be able to see the given values in the measurement
    time_0 = sample_start * dt_s
    time = np.arange(samples) * dt_s + time_0
    x = np.zeros(samples)
    maxNyquistHz = 1/(2.0*dt_s)
    sine_freq_Hz = 0.000001 # on a E12 point, not equal to fs so we can see errors, just in case
    while sine_freq_Hz < 0.8 * maxNyquistHz: # only sines below nyquist limit
      x += sine_amp_V_rms*np.sqrt(2)*np.sin(2*np.pi*sine_freq_Hz*time)
      print(sine_freq_Hz)
      sine_freq_Hz = 10.0 * sine_freq_Hz # a sine every decade
    x += np.random.normal(scale=noise_density_V_sqrtHz*np.sqrt(1/(2.0*dt_s)), size=samples)
    return(x)

x = process(sample_start=0, samples=100000, dt_s=dt_s, sine_amp_V_rms = 0.01, noise_density_V_sqrtHz = 0.001)

if True:
    f, Pxx_den = signal.periodogram(x, 1/dt_s, window='hamming', detrend='linear')
    plt.loglog(f, np.sqrt(Pxx_den))
    plt.ylim([1e-7, 1e2])
    plt.xlabel('frequency [Hz]')
    plt.ylabel('LSD[V/sqrt(Hz)]')
    plt.show()
    print(np.sqrt(np.mean(Pxx_den)))

if True:
    fig, ax = plt.subplots()
    ax.plot(x)
    ax.set(xlabel='sample', ylabel='V', title='Tralala')
    ax.grid()
    plt.show()




