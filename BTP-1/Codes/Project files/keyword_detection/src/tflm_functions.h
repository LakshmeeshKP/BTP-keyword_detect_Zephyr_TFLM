#ifndef TFLM_FUNCTIONS_H
#define TFLM_FUNCTIONS_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void perform_inference(float in[125][13]);

#ifdef __cplusplus
}
#endif

#endif