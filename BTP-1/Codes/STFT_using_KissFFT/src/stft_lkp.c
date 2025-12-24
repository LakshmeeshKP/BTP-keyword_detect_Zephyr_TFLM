#include <stdint.h>
#include "tools/kiss_fftr.h"
#include "stft_lkp.h"
#include <zephyr/kernel.h>
#include <math.h>


void print_array(float arr[], int size) {
    for (int i = 0; i < size; i++) {
        printf("%f ",arr[i]);
        k_msleep(1);
    }
    printf("\n");
}

//windowing function
void apply_window(float input[], const float window[], int size) {
    for (int i = 0; i < size; i++) {
        input[i] = input[i] * window[i];
    }
}

// Initializer
void stft_init(stft_lkp_cfg *stft_cfg, int fft_size, int hop_size, int sample_rate, float window[], char fft_cfg_buffer[], size_t *fft_cfg_buffer_len) {
    stft_cfg->cfg = kiss_fftr_alloc(fft_size, 0, fft_cfg_buffer, fft_cfg_buffer_len);
    // printk("cfg address: %p\n", stft_cfg->cfg);
    printk("NOTE: fft_cfg_buffer_len should be atleast %d\n", (int)*fft_cfg_buffer_len);
    stft_cfg->fft_size = fft_size;       
    stft_cfg->hop_size = hop_size;       
    stft_cfg->sample_rate = sample_rate;    
    stft_cfg->window = window; 
    stft_cfg->out_buffer = malloc((fft_size / 2 + 1) * sizeof(kiss_fft_cpx));
    stft_cfg->in_buffer = malloc((fft_size) * sizeof(float));
}

// STFT computation
void stft(stft_lkp_cfg *stft_cfg, const int *samples, float *output) {
    int frames=(stft_cfg->sample_rate / stft_cfg->hop_size);  //assume input is 1sec long
    int output_size=stft_cfg->fft_size / 2 + 1; 

    for(int i=0; i < frames-1; i++) {
        for(int j=0; j < stft_cfg->fft_size; j++) {
            stft_cfg->in_buffer[j]=samples[i * stft_cfg->hop_size + j]/32768.0f; //assume input is int16
        }

        apply_window(stft_cfg->in_buffer, stft_cfg->window, stft_cfg->fft_size);

        kiss_fftr(stft_cfg->cfg, stft_cfg->in_buffer, stft_cfg->out_buffer);
        for (int k = 0; k < output_size; k++) {
            float re = stft_cfg->out_buffer[k].r;
            float im = stft_cfg->out_buffer[k].i;
            output[i*output_size + k] = sqrt(re*re + im*im);
        }
    }
}

//deallocate buffers
void stft_free(stft_lkp_cfg *stft_cfg) {
    if (stft_cfg->cfg) {
        if (stft_cfg->out_buffer) {
            free(stft_cfg->out_buffer);
            stft_cfg->out_buffer = NULL;
        }
        if (stft_cfg->in_buffer) {
            free(stft_cfg->in_buffer);
            stft_cfg->in_buffer = NULL;
        }
        free(stft_cfg->cfg);
        stft_cfg->cfg = NULL;
    }
}