#ifndef CONSTANTS_H
#define CONSTANTS_H

#include "arm_math.h"

extern uint32_t mfcc_init_fftLen;
extern uint32_t nbMelFilters; 
extern uint32_t nbDctOutputs; 

extern const uint32_t filterPos[20];
extern const uint32_t filterLengths[20];
extern const float32_t dctCoefs[260];
extern const float32_t filterCoefs[236];
extern const float32_t windowCoefs[256];

extern volatile float32_t temp[258]; 

#endif