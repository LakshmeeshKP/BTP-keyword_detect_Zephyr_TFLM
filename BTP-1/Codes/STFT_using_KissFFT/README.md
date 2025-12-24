This folder contains an implementation of the Short-Time Fourier Transform (STFT) using the KISS FFT (kissfft.h) library.
Do note that the main project, heyword_detection, uses the CMSIS-DSP library; this implementation is provided as an independent reference.

This implementation makes the following assumptions:

1. The audio input duration is 1 second.

2. The input signal is of type int16_t, with a value range of [-32768, 32767].



