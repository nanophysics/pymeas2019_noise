import logging

import numpy as np

import program
import program_fir

import library_path

logger = logging.getLogger("logger")

np.random.seed(47)

DT_S = 2 ** 5 / 125e6


class TestSignal:
    def __init__(self, sine_amp_V_rms, noise_density_V_sqrtHz):
        self.sine_amp_V_rms = sine_amp_V_rms
        self.noise_density_V_sqrtHz = noise_density_V_sqrtHz
        self.list_frequencies = []
        sine_freq_Hz = 0.000001  # on a E12 point, not equal to fs so we can see errors, just in case
        maxNyquistHz = 1 / (2.0 * DT_S)
        while sine_freq_Hz < 0.8 * maxNyquistHz:  # only sines below nyquist limit
            self.list_frequencies.append(sine_freq_Hz)
            logger.info(f"sine_freq_Hz: {sine_freq_Hz}")
            sine_freq_Hz = 10.0 * sine_freq_Hz  # a sine every decade

    def calculate(self, dt_s, sample_start, push_size_samples):
        # test signal to test the algorythm
        # produces sines every decade with added white noise
        # you should be able to see the given values in the measurement
        time_0 = sample_start * dt_s
        logger.info(f"time s: {time_0:0.1f}")
        time = np.arange(push_size_samples) * dt_s + time_0
        signal = np.random.normal(scale=self.noise_density_V_sqrtHz * np.sqrt(1 / (2.0 * dt_s)), size=push_size_samples)
        for sine_freq_Hz in self.list_frequencies:
            signal += self.sine_amp_V_rms * np.sqrt(2) * np.sin(2 * np.pi * sine_freq_Hz * time)
        assert len(signal) == push_size_samples
        # logger.info('.', end='')
        return signal


def main():
    library_path.init_logger_measurement()

    class SampleProcessConfig:
        def __init__(self):
            self.fir_count = 20
            self.fir_count_skipped = 0
            self.stepname = "slow"

    signal = TestSignal(sine_amp_V_rms=1e-4, noise_density_V_sqrtHz=1e-7)

    config = SampleProcessConfig()
    sp = program_fir.SampleProcess(config=config, directory_raw=program.MEASUREMENT_ACTUAL / "raw-green-syntetic")
    i = program_fir.InSyntetic(sp.output, signal=signal, dt_s=DT_S, time_total_s=10.0)
    i.process()
    logger.info("Done")


if __name__ == "__main__":
    main()
