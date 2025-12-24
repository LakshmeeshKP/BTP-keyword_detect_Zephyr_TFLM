/*
Note: 
Assumption made:
1.input is 1sec long 
2.input datatype is int16 with range [-32768,32767].
*/

#ifndef STFT_LKP_H
#define STFT_LKP_H

#include <stdint.h>
#include "tools/kiss_fftr.h"

typedef struct {
    int fft_size;       
    int hop_size;       
    int sample_rate;    
    float *window;
    kiss_fftr_cfg cfg;  
    kiss_fft_cpx* out_buffer;
    float* in_buffer;
} stft_lkp_cfg;


void print_array(float arr[], int size);

// Initializer
void stft_init(stft_lkp_cfg *stft_cfg, int fft_size, int hop_size, int sample_rate, float window[], char fft_cfg_buffer[], size_t *fft_cfg_buffer_len);

// STFT computation
void stft(stft_lkp_cfg *stft_cfg, const int *samples, float *output);

//deallocate buffers
void stft_free(stft_lkp_cfg *stft_cfg);

#endif 