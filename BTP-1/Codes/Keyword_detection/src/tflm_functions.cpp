#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "tflm_functions.h"
#include "model_data_small.hpp"

#include <tensorflow/lite/micro/micro_mutable_op_resolver.h>
#include <tensorflow/lite/micro/micro_log.h>
#include <tensorflow/lite/micro/micro_interpreter.h>
#include <tensorflow/lite/micro/system_setup.h>
#include <tensorflow/lite/schema/schema_generated.h>

#include <zephyr/random/random.h>
#include <zephyr/sys/time_units.h>
#include <zephyr/kernel.h>

// #include "tensorflow/lite/micro/tflite_bridge/micro_error_reporter.h"
// #include "tensorflow/lite/micro/testing/micro_test.h"
//#include <zephyr/logging/log.h>

namespace {
	const tflite::Model *model = nullptr;
	tflite::MicroInterpreter *interpreter = nullptr;
	TfLiteTensor *input = nullptr;
	TfLiteTensor *output = nullptr;
	static constexpr int kTensorArenaSize = 30*1024; //80kb //in bytes 
	alignas(16) uint8_t tensor_arena[kTensorArenaSize];

	//tflite::MicroErrorReporter micro_error_reporter;
	//tflite::ErrorReporter* error_reporter = &micro_error_reporter;
	
}  /* namespace */

void perform_inference(float in[125][13]){
	
	model = tflite::GetModel(model_data_small);
	if (model->version() != TFLITE_SCHEMA_VERSION) {
		MicroPrintf("Model provided is schema version %d not equal "
					"to supported version %d.",
					model->version(), TFLITE_SCHEMA_VERSION);
		return;
	}

	tflite::MicroMutableOpResolver <9> resolver;
	resolver.AddExpandDims();
	resolver.AddConv2D();
	resolver.AddReshape();
	resolver.AddMaxPool2D();
	resolver.AddShape();
	resolver.AddStridedSlice();
	resolver.AddPack();
	resolver.AddSoftmax();
	resolver.AddFullyConnected();

	/* Build an interpreter to run the model with. */
	static tflite::MicroInterpreter static_interpreter(model, resolver, tensor_arena, kTensorArenaSize);
	interpreter = &static_interpreter;

	/* Allocate memory from the tensor_arena for the model's tensors. */
	TfLiteStatus allocate_status = interpreter->AllocateTensors();
	if (allocate_status != kTfLiteOk) {
		MicroPrintf("AllocateTensors() failed");
		return;
	}   
	MicroPrintf("Arena used bytes: %d\n", interpreter->arena_used_bytes());

	input = interpreter->input(0);

	MicroPrintf("input dims size: %d\n", input->dims->size);
	MicroPrintf("input dim 0: %d\n", input->dims->data[0]);
	MicroPrintf("input dim 1: %d\n", input->dims->data[1]);
	MicroPrintf("input dim last: %d\n", input->dims->data[input->dims->size - 1]);
	MicroPrintf("input type: %d\n", input->type);

	output = interpreter->output(0);

	MicroPrintf("tflm init success\n");
	

	constexpr int kFeatureElementCount = 1625;

	MicroPrintf("input tensor bytes: %d\n", input->bytes);

	float in_scale = input->params.scale, out_scale = output->params.scale;
	int32_t in_zp = input->params.zero_point, out_zp = output->params.zero_point;
	
	for(int i=0; i<125; i++){
		for (int j=0; j<13; j++){
			int8_t val = (int8_t)(round(in[i][j] / in_scale) + in_zp);
			if (val > 127) val = 127;
			if (val < -128) val = -128;
			in[i][j] = val;
		}
	}

	std::copy_n(&in[0][0], kFeatureElementCount,tflite::GetTensorData<int8_t>(input));
	
	MicroPrintf("invoke status: %d", interpreter->Invoke());

	float y[8];
	int prediction = -1;
	MicroPrintf("predictions:\n");
	for (int i = 0; i<8; i++) {
		y[i] =(tflite::GetTensorData<int8_t>(output)[i] - out_zp) * out_scale;
		MicroPrintf("output %d: %f\n", i, y[i]);
		if (y[i]>0.6f) prediction = i;
	}
	switch(prediction){
	case 0:
	MicroPrintf("Detected keyword: down\n");
	break;
	case 1:
	MicroPrintf("Detected keyword: go\n");
	break;		
	case 2:
	MicroPrintf("Detected keyword: left\n");
	break;
	case 3:		
	MicroPrintf("Detected keyword: no\n");
	break;
	case 4:
	MicroPrintf("Detected keyword: right\n");	
	break;
	case 5:
	MicroPrintf("Detected keyword: stop\n");
	break;
	case 6:
	MicroPrintf("Detected keyword: up\n");	
	break;
	case 7:
	MicroPrintf("Detected keyword: yes\n");
	break;
	default:
	MicroPrintf("None\n");
	break;
	}

	return;
}


