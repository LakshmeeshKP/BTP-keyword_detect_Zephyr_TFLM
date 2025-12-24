/*
 * Copyright (c) 2020 Libre Solar Technologies GmbH
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/util.h>
#include "mic_functions.h"

#include <zephyr/drivers/timer/system_timer.h>
#include <zephyr/sys/clock.h>
#include <zephyr/sys/time_units.h>

//safety check to see if zephyr_user is defined and io_channels is mentioned
#if !DT_NODE_EXISTS(DT_PATH(zephyr_user)) || \
	!DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
#error "No suitable devicetree overlay specified"
#endif

#define DT_SPEC_AND_COMMA(node_id, prop, idx) \
	ADC_DT_SPEC_GET_BY_IDX(node_id, idx),

/* Data of ADC io-channels specified in devicetree. */
static const struct adc_dt_spec adc_channels[] = {
	DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), io_channels,
			     DT_SPEC_AND_COMMA)
};


int err;
uint16_t buf;
// int32_t val_mv;
struct adc_sequence sequence = {
	.buffer = &buf,
	/* buffer size in bytes, not number of samples */
	.buffer_size = sizeof(buf),
};

//struct 	k_poll_signal adc_signal;

uint16_t init_mic(void)
{
	if (!adc_is_ready_dt(&adc_chan	nels[0])) {
		printk("ADC controller device %s not ready\n", adc_channels[0].dev->name);
		return 0;
	}

	err = adc_channel_setup_dt(&adc_channels[0]);
	if (err < 0) {
		printk("Could not setup channel #%d (%d)\n", 0, err);
		return 0;
	}
	printk("mic init success\n");
	
	(void)adc_sequence_init_dt(&adc_channels[0], &sequence);
	return 0;
}

uint16_t read_mic(void){

	// (void)adc_sequence_init_dt(&adc_channels[0], &sequence);

	err = adc_read_dt(&adc_channels[0], &sequence);
	//err = adc_read_async(&adc_channels[0], &sequence, &adc_signal);
	if (err < 0) {
		printk("Could not read (%d)\n", err);
	}
	return buf;

}

//for sampling of audio (can work for upto ~4 seconds)
void sample_audio_int(uint16_t *out, int samp_rate, int time){
	// // int32_t t_i,delta;
	// // int32_t samp_delay = 1000000/samp_rate;  //us delay between samples for 16kHz
	// uint16_t iters=samp_rate*time;

	// printf("start sampling\n");
	// for (uint16_t i=0; i<iters; i+=2){
	// 	k_usleep(100);
	// 	out[i] = read_mic();
	// 	// out[i+1]=out[i]; //duplicate alternate samples to emulate 16kHz
	// 	//k_busy_wait(20);
	// }
	// for (uint16_t i=0; i<iters; i+=2){
	// 	out[i+1]=out[i]; //duplicate alternate samples to emulate 16kHz
	// }

	// // LOG_INF("end sampling");
	// printk("end sampling\n");

	int32_t t_i;
	int32_t samp_delay = 1000000/samp_rate;  //us delay between samples for 16kHz
	uint16_t iters=samp_rate*time;
	printk("check mic\n");
	// LOG_INF("check mic");
	
	uint32_t start_cycles = k_cycle_get_32();
	out[0] = read_mic(); 
	uint32_t delta_cycles = k_cycle_get_32() - start_cycles;
	uint32_t delay_time = k_cyc_to_us_floor32((uint64_t)delta_cycles);

	printk("delay time: %d us\n", delay_time);

	// LOG_INF("start sampling");
	printk("start sampling\n");
	for (uint16_t i=1; i<iters; i++){
		//k_usleep(100);
		k_usleep(100);
		out[i] = read_mic();
	}
	// LOG_INF("end sampling");
	printk("end sampling\n");
}
