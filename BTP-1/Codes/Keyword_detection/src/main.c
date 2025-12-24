#include <zephyr/kernel.h>
#include <zephyr/sys/clock.h>
// #include <zephyr/drivers/timer/system_timer.h>
#include <stdio.h>
#include "constants.h"
#include "mic_functions.h"
#include "tflm_functions.h"

arm_status status;
arm_mfcc_instance_f32 mfcc_inst;

//base,idx,input_normalised[],temp,mfcc_frame[],

void mfcc_init(void);
void get_mfcc_frame(float *input, float *output);
void get_spectrogram(uint16_t input[16000], float output[125][13]);

uint16_t samples[16000];
float32_t spectrogram[125][13];
volatile float32_t input_normalised[256]; 
volatile float32_t mfcc_frame[256];
// float32_t temp[258];
volatile int base;
volatile int idx;
    
int main(void){
    k_sleep(K_MSEC(5000));
    init_mic();
    
    mfcc_init();
    // status = arm_mfcc_init_f32(&mfcc_inst, mfcc_init_fftLen, nbMelFilters, nbDctOutputs, dctCoefs, filterPos, filterLengths, filterCoefs, windowCoefs);
    // if (status != ARM_MATH_SUCCESS) {
    //     printf("init failed!\n");
    //     while(1){}; 
    // }
    // printf("mfcc init success\n");
    
    while(1){
        printf("recording in 3..\n");
        //k_busy_wait(1000000);
        k_sleep(K_MSEC(1000));
        printf("recording in 2..\n");
        k_sleep(K_MSEC(1000));
        // k_busy_wait(1000000);
        printf("recording in 1..\n");
        k_sleep(K_MSEC(1000));
        // k_busy_wait(1000000);
        printf("start speaking..\n");
        
        sample_audio_int(samples, 16000, 1);

        // printf("start sampling\n");
        // for (uint16_t i=0; i<16000; i+=2){
        //     k_usleep(100);
        //     processed_samples[i] = read_mic();
        // }
        // for (uint16_t i=0; i<16000; i+=2){
        //     processed_samples[i+1]=processed_samples[i]; //duplicate alternate samples to emulate 16kHz
        // }
        
        printf("Recording done\n");
        
        get_spectrogram(samples, spectrogram); 
        // for (int i = 0; i < 125; i++) {
        //     int base = i * 128;
        //     for (int j = 0; j < 256; j++) {
        //         int idx=base+j;
        //         input_normalised[j] = (idx < 16000) ? (float)(processed_samples[idx]/32768.0f - 1.0f) : 0.0f;
        //         //if(i==124) printf("%d ",round(input_normalised[i]));
        //     }
        //     printf("frame: %d start\n", i);
        //     if (i==124) printf("c1\n");
        //     //get_mfcc_frame(input_normalised, mfcc_frame);
        //     arm_mfcc_f32(&mfcc_inst, input_normalised, mfcc_frame, temp);
        //     //memset(input_normalised, 0, sizeof(input_normalised));  
        //     if (i==124) printf("c2\n");
        //     for (int j = 0; j < 13; j++) {
        //         spectrogram[i][j] = mfcc_frame[j];
        //     }   
        //     printf("frame: %d\n end", i);
        // }
        
                
        printk("start inference\n");

        perform_inference(spectrogram);

        k_sleep(K_MSEC(5000));
    }

    return 0;
}


void mfcc_init(void){
    status = arm_mfcc_init_f32(&mfcc_inst, mfcc_init_fftLen, nbMelFilters, nbDctOutputs, dctCoefs, filterPos, filterLengths, filterCoefs, windowCoefs);
    if (status != ARM_MATH_SUCCESS) {
        printf("init failed!\n");
        while(1){}; 
    }
    printf("mfcc init success\n");
}


//input: one frame of samples     output: one frame of mfcc
// void get_mfcc_frame(float *input, float *output){   //for knowledge: alternate void get_mfcc_frame(float *input, float *output, int input_len, int output_len)
//     arm_mfcc_f32(&mfcc_inst, input, output, temp);
// }

//base,idx,input_normalised[],temp,mfcc_frame[],
void get_spectrogram(uint16_t input[16000], float output[125][13]){
    for (int i = 0; i < 125; i++) {
        base = i * 128;
        for (int j = 0; j < 256; j++) {
            idx=base+j;
            input_normalised[j] = (idx < 16000) ? (float)(input[idx]/32768.0f - 1.0f) : 0.01f;
            printk("%d ",(int)round(input_normalised[j]*10000.0f));
        }
        
        arm_mfcc_f32(&mfcc_inst, input_normalised, mfcc_frame, temp); 
        if (i==124) printf("check mfcc\n");
        for (int k = 0; k < 13; k++) {
            output[i][k] = mfcc_frame[k];
        }   
        printf("frame: %d end\n", i);
    }
}
