This folder includes the implementation of STFT using kissfft.h library. Note that the main project "heyword_detection" uses CMSIS-DSP library, and not this implementation. 


Assumptions made in stft_lkp.c :

1.audio input is 1sec long

2.input datatype is int16 with range [-32768,32767]



