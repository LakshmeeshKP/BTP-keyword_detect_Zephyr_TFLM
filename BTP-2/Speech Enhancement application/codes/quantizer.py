import torch
import tensorflow as tf
import litert_torch
import sys
import os

# Tell Python to also look inside the 'stream' folder
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stream'))

from stream.gtcrn_stream import StreamGTCRN

device = torch.device("cpu")

# 1. Instantiate the hollow stream model (Takes < 1 second)
# stream_model = StreamGTCRN().to(device).eval()
stream_model = StreamGTCRN().to(device)

# 2. THE HOLY GRAIL: Force PyTorch into TFLite's native NHWC layout
stream_model = stream_model.to(memory_format=torch.channels_last)
stream_model.eval()

# # swap prelu with relu to remove SELECT_V2 error during quantization. 
# def replace_prelu_with_relu(module):
#     for name, child in module.named_children():
#         if isinstance(child, torch.nn.PReLU):
#             setattr(module, name, torch.nn.ReLU())
#         else:
#             replace_prelu_with_relu(child)
# replace_prelu_with_relu(stream_model)

# # 2. Create the dummy inputs for the initial trace
# dummy_input = torch.randn(1, 257, 1, 2, device=device) 
# conv_cache = torch.zeros(2, 1, 16, 16, 33, device=device)
# tra_cache = torch.zeros(2, 3, 1, 1, 16, device=device)
# inter_cache = torch.zeros(2, 1, 33, 16, device=device)
# 4. Create a dummy input tensor
# dummy_input = torch.randn(1, 1, 16000) 

# dummy_input = torch.randn(1, 257, 1, 2, device=device).to(memory_format=torch.channels_last) #example shape for STFT input (Batch, Freq_bins, Time_frames, Channels)
dummy_input = torch.randn(2, 257, 1, 2, device=device).to(memory_format=torch.channels_last) #example shape for STFT input (Batch, Freq_bins, Time_frames, Channels)

# ENCODER CACHES (old)
# c_en1 = torch.zeros(1, 16, 2, 33).to(memory_format=torch.channels_last)   # Length 2
# c_en2 = torch.zeros(1, 16, 4, 33).to(memory_format=torch.channels_last)   # Length 4
# c_en3 = torch.zeros(1, 16, 10, 33).to(memory_format=torch.channels_last)  # Length 10
c_en1 = torch.zeros(2, 16, 2, 33).to(memory_format=torch.channels_last)   # Length 2
c_en2 = torch.zeros(2, 16, 4, 33).to(memory_format=torch.channels_last)   # Length 4
c_en3 = torch.zeros(2, 16, 10, 33).to(memory_format=torch.channels_last)  # Length 10
# ENCODER CACHES (Now NHWC)
# # Old shape: (1, 16, 2, 33) -> New shape: (1, 2, 33, 16)
# c_en1 = torch.zeros(1, 2, 33, 16)
# c_en2 = torch.zeros(1, 4, 33, 16)
# c_en3 = torch.zeros(1, 10, 33, 16)

# t_en1 = torch.zeros(1, 1, 16)       # Hidden State 1
# t_en2 = torch.zeros(1, 1, 16)       # Hidden State 2
# t_en3 = torch.zeros(1, 1, 16)       # Hidden State 3
t_en1 = torch.zeros(1,2, 16)       # Hidden State 1
t_en2 = torch.zeros(1,2, 16)       # Hidden State 2
t_en3 = torch.zeros(1,2, 16)       # Hidden State 3

# RNN CACHES
# i_rnn1 = torch.zeros(1, 33, 16)     # RNN State 1
# i_rnn2 = torch.zeros(1, 33, 16)     # RNN State 2
i_rnn1 = torch.zeros(1,66,16)     # RNN State 1
i_rnn2 = torch.zeros(1,66,16)     # RNN State 2

# DECODER CACHES (old)
# c_de1 = torch.zeros(1, 16, 10, 33).to(memory_format=torch.channels_last)  # Length 10 (Matches en3)
# c_de2 = torch.zeros(1, 16, 4, 33).to(memory_format=torch.channels_last)  # Length 4  (Matches en2)
# c_de3 = torch.zeros(1, 16, 2, 33).to(memory_format=torch.channels_last)   # Length 2  (Matches en1)
c_de1 = torch.zeros(2, 16, 10, 33).to(memory_format=torch.channels_last)  # Length 10 (Matches en3)
c_de2 = torch.zeros(2, 16, 4, 33).to(memory_format=torch.channels_last)  # Length 4  (Matches en2)
c_de3 = torch.zeros(2, 16, 2, 33).to(memory_format=torch.channels_last)   # Length 2  (Matches en1)
# # DECODER CACHES (Now NHWC)
# c_de1 = torch.zeros(1, 10, 33, 16)
# c_de2 = torch.zeros(1, 4, 33, 16)
# c_de3 = torch.zeros(1, 2, 33, 16)

# t_de1 = torch.zeros(1, 1, 16)       # Hidden State 4
# t_de2 = torch.zeros(1, 1, 16)       # Hidden State 5
# t_de3 = torch.zeros(1, 1, 16)       # Hidden State 6
t_de1 = torch.zeros(1,2, 16)       # Hidden State 4
t_de2 = torch.zeros(1,2, 16)       # Hidden State 5
t_de3 = torch.zeros(1,2, 16)       # Hidden State 6




# tfl_flags = {
#     'optimizations': [tf.lite.Optimize.DEFAULT]
# }
# 3. Create the Representative Dataset Generator for Calibration
# (TFLite's C++ backend expects lists of standard NumPy arrays)
def representative_data_gen():
    for _ in range(10):
        yield {
            "args_0": torch.randn(2, 257, 1, 2).to(memory_format=torch.channels_last),   # mix
            # "args_0": torch.randn(1, 257, 1, 2).to(memory_format=torch.channels_last),   # mix
            
            # ENCODER CACHES
            # "args_1": torch.zeros(1, 16, 2, 33).to(memory_format=torch.channels_last),   # c_en1
            # "args_2": torch.zeros(1, 16, 4, 33).to(memory_format=torch.channels_last),   # c_en2
            # "args_3": torch.zeros(1, 16, 10, 33).to(memory_format=torch.channels_last),  # c_en3
            # "args_4": torch.zeros(1, 1, 16),       # t_en1
            # "args_5": torch.zeros(1, 1, 16),       # t_en2 
            # "args_6": torch.zeros(1, 1, 16),       # t_en3
            "args_1": torch.zeros(2, 16, 2, 33).to(memory_format=torch.channels_last),   # c_en1
            "args_2": torch.zeros(2, 16, 4, 33).to(memory_format=torch.channels_last),   # c_en2
            "args_3": torch.zeros(2, 16, 10, 33).to(memory_format=torch.channels_last),  # c_en3
            "args_4": torch.zeros(1,2, 16),       # t_en1
            "args_5": torch.zeros(1,2, 16),       # t_en2 
            "args_6": torch.zeros(1,2, 16),       # t_en3
            

            # RNN / TCN CACHES
            # "args_7": torch.zeros(1, 33, 16),      # i_rnn1
            # "args_8": torch.zeros(1, 33, 16),      # i_rnn2
            "args_7": torch.zeros(1,66,16),      # i_rnn1
            "args_8": torch.zeros(1,66,16),      # i_rnn2

            # DECODER CACHES
            # "args_9": torch.zeros(1, 16, 10, 33).to(memory_format=torch.channels_last),  # c_de1
            # "args_10": torch.zeros(1, 16, 4, 33).to(memory_format=torch.channels_last),  # c_de2
            # "args_11": torch.zeros(1, 16, 2, 33).to(memory_format=torch.channels_last),  # c_de3
            # "args_12": torch.zeros(1, 1, 16),      # t_de1
            # "args_13": torch.zeros(1, 1, 16),      # t_de2
            # "args_14": torch.zeros(1, 1, 16)       # t_de3
            "args_9": torch.zeros(2, 16, 10, 33).to(memory_format=torch.channels_last),  # c_de1
            "args_10": torch.zeros(2, 16, 4, 33).to(memory_format=torch.channels_last),  # c_de2
            "args_11": torch.zeros(2, 16, 2, 33).to(memory_format=torch.channels_last),  # c_de3
            "args_12": torch.zeros(1,2, 16),      # t_de1
            "args_13": torch.zeros(1,2, 16),      # t_de2
            "args_14": torch.zeros(1,2, 16)       # t_de3
        }

        # yield {
        #     "dummy_input": torch.randn(1, 257, 1, 2).numpy(),
            
        #     # ENCODER CACHES
        #     "c_en1": torch.zeros(1, 16, 2, 33).numpy(),
        #     "c_en2": torch.zeros(1, 16, 4, 33).numpy(),
        #     "c_en3": torch.zeros(1, 16, 10, 33).numpy(),
        #     "t_en1": torch.zeros(1, 1, 16).numpy(),
        #     "t_en2": torch.zeros(1, 1, 16).numpy(),
        #     "t_en3": torch.zeros(1, 1, 16).numpy(),

        #     # RNN / TCN CACHES
        #     "i_rnn1": torch.zeros(1, 33, 16).numpy(),
        #     "i_rnn2": torch.zeros(1, 33, 16).numpy(),

        #     # DECODER CACHES
        #     "c_de1": torch.zeros(1, 16, 10, 33).numpy(),
        #     "c_de2": torch.zeros(1, 16, 4, 33).numpy(),
        #     "c_de3": torch.zeros(1, 16, 2, 33).numpy(),
        #     "t_de1": torch.zeros(1, 1, 16).numpy(),
        #     "t_de2": torch.zeros(1, 1, 16).numpy(),
        #     "t_de3": torch.zeros(1, 1, 16).numpy()
        # }
        
        # yield [
        #     torch.randn(1, 257, 1, 2, device=device).numpy(),
            
        #     # ENCODER CACHES
        #     torch.zeros(1, 16, 2, 33).numpy(),   # Length 2
        #     torch.zeros(1, 16, 4, 33).numpy(),   # Length 4
        #     torch.zeros(1, 16, 10, 33).numpy(),  # Length 10
        #     torch.zeros(1, 1, 16).numpy(),       # Hidden State 1
        #     torch.zeros(1, 1, 16).numpy(),       # Hidden State 2
        #     torch.zeros(1, 1, 16).numpy(),       # Hidden State 3

        #     # RNN / TCN CACHES
        #     torch.zeros(1, 33, 16).numpy(),     # RNN State 1
        #     torch.zeros(1, 33, 16).numpy(),     # RNN State 2

        #     # DECODER CACHES
        #     torch.zeros(1, 16, 10, 33).numpy(),  # Length 10 (Matches en3)
        #     torch.zeros(1, 16, 4, 33).numpy(),   # Length 4  (Matches en2)
        #     torch.zeros(1, 16, 2, 33).numpy(),   # Length 2  (Matches en1)
        #     torch.zeros(1, 1, 16).numpy(),       # Hidden State 4
        #     torch.zeros(1, 1, 16).numpy(),       # Hidden State 5
        #     torch.zeros(1, 1, 16).numpy()        # Hidden State 6
        # ]

# 4. Configure the exact LiteRT flags for Full INT8
target_spec = tf.lite.TargetSpec()
target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

tfl_flags = {
    'optimizations': [tf.lite.Optimize.DEFAULT],
    'representative_dataset': representative_data_gen,
    'target_spec': target_spec,
    'inference_input_type': tf.int8,
    'inference_output_type': tf.int8,
    'experimental_full_integer_quantization': True
}

print("Tracing, quantizing, and converting directly to INT8 LiteRT...")

# 5. Convert using LiteRT Torch with the quantization flags injected
try:
    # edge_model = litert_torch.convert(
    #     stream_model, 
    #     (dummy_input, conv_cache, tra_cache, inter_cache),
    #     _ai_edge_converter_flags=tfl_flags
    # )

    edge_model = litert_torch.convert(
        stream_model, 
        (dummy_input, 
        c_en1, c_en2, c_en3, t_en1, t_en2, t_en3, 
         i_rnn1, i_rnn2, 
         c_de1, c_de2, c_de3, t_de1, t_de2, t_de3), 
         _ai_edge_converter_flags=tfl_flags
    )
    
    # 6. Save the perfectly quantized file
    edge_model.export("gtcrn_lkp_quantized.tflite")
    print("Success! Saved as gtcrn_lkp_quantized.tflite")

except Exception as e:
    print(f"Conversion failed: {e}")