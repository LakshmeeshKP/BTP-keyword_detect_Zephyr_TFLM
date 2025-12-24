#ifndef MIC_FUNCTIONS_H
#define MIC_FUNCTIONS_H


#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

uint16_t init_mic(void);
uint16_t read_mic(void);
//for sampling of audio (can work for upto ~4 seconds) 
//for int output; range [-2^8,2^8]
// void sample_audio_int(uint16_t *out, int samp_rate, int time);

#ifdef __cplusplus
}
#endif

#endif 