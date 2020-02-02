# pymeas2019 Background Info

pymeas2019_noise estimates the LSD (amplitude spectral density or linear spectral density) of a signal sampled with a picoscope.
It works only for "stochastic noise" signals. Signals with single events or sinusoidal parts are not useful.

At high frequencies this is done by DFT of parts of the sampled signal.
At low frequencies this is done by overlapped segmented averaging of modified periodograms. (modified -> hamming window)
To geht to low sample rates the signal is downsampled again and again. 

To cover a large frequencie range, it was neccesary to involve different low pass filters and to use different sample rates with the picoscope oscilloscope.

Recommended literature: Spectrum and spectral density estimation by the Discrete Fourier
transform (DFT), including a comprehensive list of window
functions and some new 
at-top windows. G. Heinzel et al 2002

