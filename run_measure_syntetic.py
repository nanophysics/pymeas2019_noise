import scipy.signal
import numpy as np

import program
import program_fir
import run_0_measure

class TestSignal:
  def __init__(self, sine_amp_V_rms, noise_density_V_sqrtHz):
    self.sine_amp_V_rms = sine_amp_V_rms
    self.noise_density_V_sqrtHz = noise_density_V_sqrtHz

  def calculate(self, dt_s, sample_start, push_size_samples):
    # test signal to test the algorythm
    # produces sines every decade with added white noise
    # you should be able to see the given values in the measurement
    time_0 = sample_start * dt_s
    time = np.arange(push_size_samples) * dt_s + time_0
    array = np.zeros(push_size_samples)
    maxNyquistHz = 1/(2.0*dt_s)
    sine_freq_Hz = 0.000001 # on a E12 point, not equal to fs so we can see errors, just in case
    while sine_freq_Hz < 0.8 * maxNyquistHz: # only sines below nyquist limit
      array += self.sine_amp_V_rms*np.sqrt(2)*np.sin(2*np.pi*sine_freq_Hz*time)
      # print(sine_freq_Hz)
      sine_freq_Hz = 10.0 * sine_freq_Hz # a sine every decade
    array += np.random.normal(scale=self.noise_density_V_sqrtHz*np.sqrt(1/(2.0*dt_s)), size=push_size_samples)
    assert len(array) == push_size_samples
    return array

if __name__ == '__main__':
  class SampleProcessConfig:
    def __init__(self):
      self.fir_count = 8
      self.fir_count_skipped = 4
      self.stepname = 'slow'

  dt_s = 1.0/run_0_measure.f2_slow_fs_hz
  signal = TestSignal(sine_amp_V_rms=0.1, noise_density_V_sqrtHz=0.1)

  config = SampleProcessConfig()
  sp = program_fir.SampleProcess(config=config, directory_raw=f'{program.MEASUREMENT_ACTUAL}/raw-green-syntetic')
  i = program_fir.InSyntetic(sp.output, signal=signal, dt_s=dt_s, time_total_s=60.0)
  i.process()
