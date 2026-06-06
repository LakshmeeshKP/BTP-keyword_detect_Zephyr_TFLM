import torch
import litert_torch
import os
import sys

# This tells Python to also look inside the 'stream' folder when searching for modules.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stream'))

# 1. Import the model architecture from the repo's code.
# (Look inside the repo's files. Usually, there is a file named 'model.py', 'gtcrn.py', or 'network.py')
# For example, if it's in a file called `gtcrn.py`, do:
from gtcrn import GTCRN 
from stream.modules.convert import convert_to_stream
from stream.gtcrn_stream import StreamGTCRN
from stream.modules.convolution import StreamConv2d, StreamConvTranspose2d

    
device = torch.device("cpu")



# 2. Instantiate the model. 
# (You may need to pass specific parameters here if the __init__ requires them, check the repo's train.py to see how they initialize it)
# model = GTCRN().to(device).eval()


# --- OPTIONAL: Load weights ---
# If you just want to check if the model fits in the Pico's SRAM, you DON'T need trained weights! 
# The memory footprint of garbage random weights is exactly the same as trained weights. 
# But if you have a checkpoint, you load it like this:
# model.load_state_dict(torch.load('checkpoints/model_trained_on_dns3.tar', map_location=device)['model'])
stream_model = StreamGTCRN().to(device).eval()
# convert_to_stream(stream_model, model)
# ------------------------------

# 3. Set to evaluation mode (CRITICAL: turns off dropout, batchnorm training, etc.)
# model.eval() #done above

# 4. Create a dummy input tensor
# dummy_input = torch.randn(1, 1, 16000) 
dummy_input = torch.randn(1, 257, 1, 2, device=device) #example shape for STFT input (Batch, Freq_bins, Time_frames, Channels)

# ENCODER CACHES
c_en1 = torch.zeros(1, 16, 2, 33)   # Length 2
c_en2 = torch.zeros(1, 16, 4, 33)   # Length 4
c_en3 = torch.zeros(1, 16, 10, 33)  # Length 10
# ENCODER CACHES (NHWC format: 1, Time, 33, 16)
# c_en1 = torch.zeros(1, 2, 33, 16)
# c_en2 = torch.zeros(1, 4, 33, 16)
# c_en3 = torch.zeros(1, 10, 33, 16)
t_en1 = torch.zeros(1, 1, 16)       # Hidden State 1
t_en2 = torch.zeros(1, 1, 16)       # Hidden State 2
t_en3 = torch.zeros(1, 1, 16)       # Hidden State 3

# RNN CACHES
i_rnn1 = torch.zeros(1, 33, 16)     # RNN State 1
i_rnn2 = torch.zeros(1, 33, 16)     # RNN State 2

# DECODER CACHES
c_de1 = torch.zeros(1, 16, 10, 33)  # Length 10 (Matches en3)
c_de2 = torch.zeros(1, 16, 4, 33)   # Length 4  (Matches en2)
c_de3 = torch.zeros(1, 16, 2, 33)   # Length 2  (Matches en1)
# DECODER CACHES (NHWC format: 1, Time, 33, 16)
# c_de1 = torch.zeros(1, 10, 33, 16)
# c_de2 = torch.zeros(1, 4, 33, 16)
# c_de3 = torch.zeros(1, 2, 33, 16)
t_de1 = torch.zeros(1, 1, 16)       # Hidden State 4
t_de2 = torch.zeros(1, 1, 16)       # Hidden State 5
t_de3 = torch.zeros(1, 1, 16)       # Hidden State 6

print("Tracing model and converting to LiteRT...")

# 5. Convert using AI Edge Torch (Direct PyTorch -> LiteRT)
try:
    # edge_model = litert_torch.convert(stream_model, (dummy_input,))
    edge_model = litert_torch.convert(
        stream_model, 
        (dummy_input, 
        c_en1, c_en2, c_en3, t_en1, t_en2, t_en3, 
         i_rnn1, i_rnn2, 
         c_de1, c_de2, c_de3, t_de1, t_de2, t_de3)
    )
    # 6. Save the file
    edge_model.export("gtcrn_lkp.tflite")
    print("Success! Saved as gtcrn_lkp.tflite")

except Exception as e:
    print(f"Conversion failed: {e}")


# import tensorflow as tf
# import numpy as np
# print("started quantisation...")


# # 1. Initialize the converter with your model and dummy inputs
# converter = litert_torch.TFLiteConverter.from_module(
#     stream_model, 
#     (dummy_input, conv_cache, tra_cache, inter_cache)
# )

# # ... [Keep your model instantiation and dummy_input setup the same] ...

# # 1. Create the Representative Dataset Generator
# # TFLite's C++ backend expects lists of standard NumPy arrays
# def representative_data_gen():
#     for _ in range(10):
#         yield [
#             torch.randn(1, 257, 1, 2, device=device).numpy(),
#             torch.zeros(2, 1, 16, 16, 33, device=device).numpy(),
#             torch.zeros(2, 3, 1, 1, 16, device=device).numpy(),
#             torch.zeros(2, 1, 33, 16, device=device).numpy()
#         ]

# # 2. Configure the exact TensorFlow Lite Converter flags for Full INT8
# target_spec = tf.lite.TargetSpec()
# target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

# tfl_flags = {
#     'optimizations': [tf.lite.Optimize.DEFAULT],
#     'representative_dataset': representative_data_gen,
#     'target_spec': target_spec,
#     'inference_input_type': tf.int8,
#     'inference_output_type': tf.int8
# }

# print("Tracing, quantizing, and converting to LiteRT...")

# try:
#     # 3. Pass the flags directly into the litert_torch convert function
#     edge_model = litert_torch.convert(
#         stream_model, 
#         args=(dummy_input, conv_cache, tra_cache, inter_cache),
#         _ai_edge_converter_flags=tfl_flags # <--- The Magic Injection!
#     )
    
#     # 4. Save the file
#     edge_model.export("gtcrn_lkp_qtz.tflite")
#     print("Success! Saved as gtcrn_lkp_qtz.tflite")

# except Exception as e:
#     print(f"Conversion failed: {e}")