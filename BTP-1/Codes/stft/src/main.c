#include <stdio.h>
#include <math.h>
#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
#include "tools/kiss_fftr.h"
#include "FFTconstants.h"
#include "stft_lkp.h"

#define CFG_BUFFER_SIZE 3000

char fft_cfg_buffer[CFG_BUFFER_SIZE];
size_t fft_cfg_buffer_len = CFG_BUFFER_SIZE;

float spectrogram[124][129];

stft_lkp_cfg stft_cfg;

int main(void){
    // printf("start");
    k_sleep(K_MSEC(3000));
    stft_init(&stft_cfg, 256, 128, 16000, hann, fft_cfg_buffer, &fft_cfg_buffer_len);
    // stft_init(&stft_cfg, 256, 64, 8000, hann, fft_cfg_buffer, &fft_cfg_buffer_len);

    stft(&stft_cfg, audio_samples, spectrogram);  

    for(int i=0; i<124; i++){
        printf("Frame %d: ", i);
        print_array(spectrogram[i], 129);
    }

    stft_free(&stft_cfg);
    return 0;
}
