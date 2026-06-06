# -*- coding: utf-8 -*-
"""
Created on Sat Dec  3 17:32:08 2022
Modified on Fri Mar  7 21:25:18 2025

@author: Xiaohuai Le, Xiaobin Rong
"""
import math

import torch
import torch.nn as nn
from typing import List, Tuple, Union

"""
When export to ONNX format, ensure that the cache is saved as a tensor, not a list.
"""

class StreamConv1d(nn.Module):
    def __init__(self,
                in_channels: int,
                out_channels: int,
                kernel_size: int,
                stride: int=1,
                padding: int=0,
                dilation: int=1,
                groups: int=1,
                bias: bool=True,
                *args, **kargs):
        super(StreamConv1d, self).__init__(*args, *kargs)
        
        assert padding == 0, "To meet the demands of causal streaming requirements"
        
        self.Conv1d = nn.Conv1d(in_channels = in_channels,
                                out_channels = out_channels,
                                kernel_size = kernel_size,
                                stride = stride,
                                padding = padding,
                                dilation = dilation,
                                groups = groups,
                                bias = bias)
    
    def forward(self, x, cache):
        """
        x:     [bs, C, T_size]
        cache: [bs, C, T_size-1]
        """
        inp = torch.cat([cache, x], dim=-1)
        oup = self.Conv1d(inp)
        out_cache = inp[..., 1:]
        return oup, out_cache

#lkp edit ver3 start : custom depth wise convolution to fix qtz
class StreamConv2d(nn.Module):
    def __init__(self, 
                 in_channels: int,
                 out_channels: int,
                 kernel_size: Union[int, Tuple[int, int]],
                 stride: Union[int, Tuple[int, int]] = 1,
                 padding: Union[str, int, Tuple[int, int]] = 0,
                 dilation: Union[int, Tuple[int, int]] = 1,
                 groups: int = 1,
                 bias: bool = True,
                 *args, **kargs):
        super().__init__(*args, **kargs)
        """
        kernel_size = [T_size, F_size] by defalut
        """
        if type(padding) is int:
            self.T_pad = padding
            self.F_pad = padding
        elif type(padding) in [list, tuple]:
            self.T_pad, self.F_pad = padding
        else:
            raise ValueError('Invalid padding size.')
        
        assert self.T_pad == 0, "To meet the demands of causal streaming requirements"
        
        self.Conv2d = nn.Conv2d(in_channels = in_channels, 
                                out_channels = out_channels,
                                kernel_size = kernel_size,
                                stride = stride,
                                padding = padding,
                                dilation = dilation,
                                groups = groups,
                                bias = bias)
#     #lkp edit : format change to nchw from nhwc
    # def forward(self, x, cache):
    #     """
    #     x: [bs, C, 1, F]
    #     cache: [bs, C, T_size-1, F]
    #     """
    #     inp = torch.cat([cache, x], dim=2)
    #     outp = self.Conv2d(inp)
    #     out_cache = inp[:,:, 1:]
    #     return outp, out_cache

#     ##lkp edit ver2 start
#     def forward(self, x, cache_nhwc):
#         """
#         x: [bs, C, 1, F] 
#         cache_nhwc: [bs, T-1, F, C] 
#         """
#         # --- RESHAPE ARMOR ---
#         # Force the TFLite compiler to put the Batch=1 dimension back!
#         C = x.shape[1]
#         F = x.shape[3]
#         # Inflate cache to strictly 4D: [1, Time, Freq, Channels]
#         cache_nhwc = cache_nhwc.contiguous().view(1, -1, F, C)
#         # Inflate x to strictly 4D: [1, Channels, Time, Freq]
#         x = x.contiguous().view(1, C, -1, F)

#         # 1. Permute safely now that we are guaranteed 4D
#         cache_nchw = cache_nhwc.permute(0, 3, 1, 2)
        
#         # 2. Concat will now succeed! (4 == 4)
#         inp = torch.cat([cache_nchw, x], dim=2)
        
#         outp = self.Conv2d(inp)
        
#         # 3. Clean slice and flip back to NHWC
#         out_cache_nhwc = inp[:, :, 1:].permute(0, 2, 3, 1)
        
#         # Armor the output cache just in case the compiler tries to squeeze it on exit
#         out_cache_nhwc = out_cache_nhwc.contiguous().view(1, -1, F, C)
        
#         return outp, out_cache_nhwc
#     ##lkp edit ver2 end
#     # #lkp edit ver1 start
#     # def forward(self, x, cache_nhwc):
#     #     """
#     #     x: [B, C, 1, F] -> NCHW
#     #     cache_nhwc: [B, T-1, F, C] -> NHWC
#     #     """
#     #     # 1. Flip x to NHWC so it matches the cache
#     #     x_nhwc = x.permute(0, 2, 3, 1) # [B, 1, F, C]
        
#     #     # 2. Concat natively in NHWC! (Time is dim=1 in NHWC)
#     #     # This completely prevents TFLite from auto-inserting Transpose nodes!
#     #     inp_nhwc = torch.cat([cache_nhwc, x_nhwc], dim=1) # [B, T, F, C]
        
#     #     # 3. Clean slice the cache in NHWC
#     #     out_cache_nhwc = inp_nhwc[:, 1:, :, :] # [B, T-1, F, C]
        
#     #     # 4. Flip the combined input to NCHW for PyTorch's math
#     #     inp_nchw = inp_nhwc.permute(0, 3, 1, 2) # [B, C, T, F]
        
#     #     # 5. Convolution (TFLite will natively fuse this into an NHWC Conv2D!)
#     #     outp = self.Conv2d(inp_nchw)
        
#     #     return outp, out_cache_nhwc
#     # #lkp edit ver1 end
#     #lkp edit end

# class StreamConv2d(nn.Module):
#     def __init__(self, 
#                  in_channels: int,
#                  out_channels: int,
#                  kernel_size: Union[int, Tuple[int, int]],
#                  stride: Union[int, Tuple[int, int]] = 1,
#                  padding: Union[str, int, Tuple[int, int]] = 0,
#                  dilation: Union[int, Tuple[int, int]] = 1,
#                  groups: int = 1,
#                  bias: bool = True,
#                  *args, **kargs):
#         super().__init__(*args, **kargs)
        
#         if type(padding) is int:
#             self.T_pad = padding
#             self.F_pad = padding
#         elif type(padding) in [list, tuple]:
#             self.T_pad, self.F_pad = padding
#         else:
#             raise ValueError('Invalid padding size.')
        
#         assert self.T_pad == 0, "To meet the demands of causal streaming requirements"
        
#         self.groups = groups

#         # --- THE SPLIT-AND-CONCAT BYPASS ---
#         if groups == 1:
#             # Normal convolution, totally safe for TFLite
#             self.convs = nn.ModuleList([
#                 nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, dilation, bias=bias)
#             ])
#         else:
#             # DEPTHWISE BYPASS: Build the groups manually!
#             assert in_channels % groups == 0
#             assert out_channels % groups == 0
#             in_per_group = in_channels // groups
#             out_per_group = out_channels // groups

#             # Create an independent standard Conv2d (groups=1) for EVERY group
#             self.convs = nn.ModuleList([
#                 nn.Conv2d(in_per_group, out_per_group, kernel_size, stride, padding, dilation, bias=bias)
#                 for _ in range(groups)
#             ])
    # #lkp edit 4: temporarily do 3d before concat then 4d before convolution
    # def forward(self, x, cache):
    #     """
    #     x: [bs, C, 1, F] -> Standard NCHW
    #     cache: [bs, C, T_size-1, F] -> Standard NCHW
    #     """
    #     # --- RESHAPE ARMOR ---
    #     # Force TFLite to maintain the 4D shape (Batch=1) before the layout optimizer strikes
    #     C = x.shape[1]
    #     F = x.shape[3]
    #     x = x.contiguous().view(1, C, -1, F)
    #     cache = cache.contiguous().view(1, C, -1, F)
    #     # ---------------------

    #     # Safe Concatenation
    #     inp = torch.cat([cache, x], dim=2)
        
    #     if self.groups == 1:
    #         outp = self.convs[0](inp)
    #     else:
    #         in_chunks = torch.chunk(inp, self.groups, dim=1)
    #         out_chunks = []
    #         for i in range(self.groups):
    #             out_chunks.append(self.convs[i](in_chunks[i]))
    #         outp = torch.cat(out_chunks, dim=1)
            
    #     out_cache = inp[:,:, 1:]
        
    #     # Armor the cache on the way out so the next layer doesn't crash!
    #     out_cache = out_cache.contiguous().view(1, C, -1, F)
        
    #     return outp, out_cache

    # def forward(self, x, cache):
    #     """
    #     x: [B, C, 1, F] -> Standard NCHW
    #     cache: [B, C, T_cache, F] -> Standard NCHW
    #     """
    #     B, C, _, F = x.shape 
    #     T_cache = cache.shape[2]

    #     # 1. THE 3D FLATTEN BYPASS
    #     # Blind the TFLite Layout Optimizer by temporarily flattening Time and Freq!
    #     cache_3d = cache.contiguous().view(B, C, T_cache * F)
    #     x_3d = x.contiguous().view(B, C, 1 * F)

    #     # 2. Concat safely in 3D (The optimizer ignores 3D arrays, so NO auto-transposes!)
    #     inp_3d = torch.cat([cache_3d, x_3d], dim=2)

    #     # 3. Inflate mathematically perfectly back to 4D 
    #     inp = inp_3d.contiguous().view(B, C, T_cache + 1, F)

    #     # 4. Standard Split-and-Concat Execution (Depthwise Bypass)
    #     if self.groups == 1:
    #         outp = self.convs[0](inp)
    #     else:
    #         in_chunks = torch.chunk(inp, self.groups, dim=1)
    #         out_chunks = []
    #         for i in range(self.groups):
    #             out_chunks.append(self.convs[i](in_chunks[i]))
    #         outp = torch.cat(out_chunks, dim=1)
            
    #     out_cache = inp[:, :, 1:, :]
        
    #     return outp, out_cache
    #lkp edit ver4 end
    #lkp edit v5 start
    def forward(self, x, cache):
        """
        x:     [B, C, 1, F] -> Standard NCHW
        cache: [B, C, T_cache, F] -> Standard NCHW
        """
        B, C = x.shape[0], x.shape[1]
        F = x.shape[3]

        # --- 1. THE DYNAMIC 3D FLATTEN BYPASS ---
        # Flatten Time and Freq into a single dimension to hide the 4D shape 
        # from the TFLite Layout Optimizer.
        cache_3d = cache.contiguous().view(B, C, -1)
        x_3d = x.contiguous().view(B, C, -1)

        # --- 2. 3D CONCATENATION ---
        # The optimizer ignores 3D arrays, so NO auto-transposes crash here!
        inp_3d = torch.cat([cache_3d, x_3d], dim=2)

        # --- 3. INFLATE TO 4D ---
        # Using -1 for the Time dimension makes this mathematically indestructible. 
        inp = inp_3d.contiguous().view(B, C, -1, F)
        
        # --- 4. STANDARD MATH ---
        outp = self.Conv2d(inp)
        out_cache = inp[:, :, 1:, :]
        
        return outp, out_cache
    #lkp edit v5 end

#lkp edit ver3 end

## Version 1 
## The inference of this implementation is slow, according to https://github.com/Xiaobin-Rong/gtcrn/issues/37
# class StreamConvTranspose2d(nn.Module):
#     def __init__(self, 
#                  in_channels: int,
#                  out_channels: int,
#                  kernel_size: Union[int, Tuple[int, int]],
#                  stride: Union[int, Tuple[int, int]] = 1,
#                  padding: Union[str, int, Tuple[int, int]] = 0,
#                  dilation: Union[int, Tuple[int, int]] = 1,
#                  groups: int = 1,
#                  bias: bool = True,
#                  *args, **kargs):
#         super().__init__(*args, **kargs)
#         """
#         kernel_size = [T_size, F_size] by default
#         stride = [T_stride, F_stride] and assert T_stride == 1
#         """
#         if type(kernel_size) is int:
#             self.T_size = kernel_size
#             self.F_size = kernel_size
#         elif type(kernel_size) in [list, tuple]:
#             self.T_size, self.F_size = kernel_size
#         else:
#             raise ValueError('Invalid kernel size.')
            
#         if type(stride) is int:
#             self.T_stride = stride
#             self.F_stride = stride
#         elif type(stride) in [list, tuple]:
#             self.T_stride, self.F_stride = stride
#         else:
#             raise ValueError('Invalid stride size.')
        
#         assert self.T_stride == 1

#         if type(padding) is int:
#             self.T_pad = padding
#             self.F_pad = padding
#         elif type(padding) in [list, tuple]:
#             self.T_pad, self.F_pad = padding
#         else:
#             raise ValueError('Invalid padding size.')
        
#         if type(dilation) is int:
#             self.T_dilation = dilation
#             self.F_dilation = dilation
#         elif type(dilation) in [list, tuple]:
#             self.T_dilation, self.F_dilation = dilation
#         else:
#             raise ValueError('Invalid dilation size.')
        
#         assert self.T_pad == (self.T_size-1) * self.T_dilation, "To meet the demands of causal streaming requirements"

#         self.ConvTranspose2d = nn.ConvTranspose2d(in_channels = in_channels, 
#                                                 out_channels = out_channels,
#                                                 kernel_size = kernel_size,
#                                                 stride = stride, 
#                                                 padding = padding,
#                                                 dilation = dilation,
#                                                 groups = groups,
#                                                 bias = bias)
        
#     def forward(self, x, cache):
#         """
#         x: [bs, C, 1, F]
#         cache: [bs, C, T_size-1, F]
#         """
#         inp = torch.cat([cache, x], dim=2)
#         outp = self.ConvTranspose2d(inp)
#         out_cache = inp[:,:, 1:]
#         return outp, out_cache

## Version 2
# #lkp edit ver3 start: custom depth wise convolution to fix qtz
class StreamConvTranspose2d(nn.Module):
    def __init__(self, 
                 in_channels: int,
                 out_channels: int,
                 kernel_size: Union[int, Tuple[int, int]],
                 stride: Union[int, Tuple[int, int]] = 1,
                 padding: Union[str, int, Tuple[int, int]] = 0,
                 dilation: Union[int, Tuple[int, int]] = 1,
                 groups: int = 1,
                 bias: bool = True,
                 *args, **kargs):
        super().__init__(*args, **kargs)
        """
        kernel_size = [T_size, F_size] by default
        stride = [T_stride, F_stride], and T_stride == 1
        """
        self.in_channels = in_channels
        self.out_channels = out_channels
        if type(kernel_size) is int:
            self.T_size = kernel_size
            self.F_size = kernel_size
        elif type(kernel_size) in [list, tuple]:
            self.T_size, self.F_size = kernel_size
        else:
            raise ValueError('Invalid kernel size.')
            
        if type(stride) is int:
            self.T_stride = stride
            self.F_stride = stride
        elif type(stride) in [list, tuple]:
            self.T_stride, self.F_stride = stride
        else:
            raise ValueError('Invalid stride size.')
        
        assert self.T_stride == 1

        if type(padding) is int:
            self.T_pad = padding
            self.F_pad = padding
        elif type(padding) in [list, tuple]:
            self.T_pad, self.F_pad = padding
        else:
            raise ValueError('Invalid padding size.')
        assert(self.T_pad == 0) 

        if type(dilation) is int:
            self.T_dilation = dilation
            self.F_dilation = dilation
        elif type(dilation) in [list, tuple]:
            self.T_dilation, self.F_dilation = dilation
        else:
            raise ValueError('Invalid dilation size.')
        
        # Implementing ConvTranspose2d using Conv2d with weight-time reversal.
        self.ConvTranspose2d = nn.Conv2d(in_channels = in_channels, 
                                        out_channels = out_channels,
                                        kernel_size = kernel_size,
                                        stride = (self.T_stride, 1), # An additional upsampling will be used in forward, if F_stride != 1
                                        padding = (self.T_pad, 0),   # An additional padding will be used in forward, if F_pad != 0
                                        dilation = dilation,
                                        groups = groups, 
                                        bias = bias)
    #this is the original forward() snippet
    def forward(self, x, cache):
        """
        x: [bs,C,1,F]
        cache: [bs,C,T-1,F]
        """
        # [bs,C,T,F]
        inp = torch.cat([cache, x], dim = 2)
        out_cache = inp[:, :, 1:]
        bs, C, T, F = inp.shape
        
        # Upsampling operation
        if self.F_stride > 1: 
            # [bs,C,T,F] -> [bs,C,T,F,1] -> [bs,C,T,F,F_stride] -> [bs,C,T,F_out]
            inp = torch.cat([inp[:,:,:,:,None], torch.zeros([bs,C,T,F,self.F_stride-1])], dim = -1).reshape([bs,C,T,-1])
            left_pad = self.F_stride - 1
            if self.F_size > 1:
                if left_pad <= self.F_size - 1:
                    inp = torch.nn.functional.pad(inp, pad = [(self.F_size - 1)*self.F_dilation-self.F_pad, (self.F_size - 1)*self.F_dilation-self.F_pad - left_pad, 0, 0])
                else:
                    # inp = torch.nn.functional.pad(inp, pad = [self.F_size - 1, 0, 0, 0])[:,:,:,: - (left_pad - self.F_stride + 1)]
                    raise(NotImplementedError)
            else:
                # inp = inp[:,:,:,:-left_pad]
                raise(NotImplementedError)

        else: # F_stride = 1
            inp = torch.nn.functional.pad(inp, pad=[(self.F_size-1)*self.F_dilation-self.F_pad, (self.F_size-1)*self.F_dilation-self.F_pad])
                
        outp = self.ConvTranspose2d(inp)
    
        return outp, out_cache
    #lkp edit : format change to nchw from nhwc ; avoid quantisation issue    
#     ##### lkp edit ver 2 start  
#     def forward(self, x, cache_nhwc):
#         # --- RESHAPE ARMOR ---
#         C = x.shape[1]
#         F = x.shape[3]
#         cache_nhwc = cache_nhwc.contiguous().view(1, -1, F, C)
#         x = x.contiguous().view(1, C, -1, F)
#         # ---------------------

#         cache_nchw = cache_nhwc.permute(0, 3, 1, 2)
#         inp = torch.cat([cache_nchw, x], dim=2)
        
#         out_cache_nhwc = inp[:, :, 1:].permute(0, 2, 3, 1)
#         out_cache_nhwc = out_cache_nhwc.contiguous().view(1, -1, F, C)
        
#         bs, C, T, F = inp.shape
        
#         # --- THE REST OF YOUR LOGIC IS UNTOUCHED ---
#         # Upsampling operation
#         if self.F_stride > 1: 
#             # [bs,C,T,F] -> [bs,C,T,F,1] -> [bs,C,T,F,F_stride] -> [bs,C,T,F_out]
#             inp = torch.cat([inp[:,:,:,:,None], torch.zeros([bs,C,T,F,self.F_stride-1])], dim = -1).reshape([bs,C,T,-1])
#             left_pad = self.F_stride - 1
#             if self.F_size > 1:
#                 if left_pad <= self.F_size - 1:
#                     inp = torch.nn.functional.pad(inp, pad = [(self.F_size - 1)*self.F_dilation-self.F_pad, (self.F_size - 1)*self.F_dilation-self.F_pad - left_pad, 0, 0])
#                 else:
#                     raise(NotImplementedError)
#             else:
#                 raise(NotImplementedError)

#         else: # F_stride = 1
#             inp = torch.nn.functional.pad(inp, pad=[(self.F_size-1)*self.F_dilation-self.F_pad, (self.F_size-1)*self.F_dilation-self.F_pad])
                
#         outp = self.ConvTranspose2d(inp)
    
#         # Return the output (NCHW) and the cache (NHWC)
#         return outp, out_cache_nhwc
#     ##### lkp edit ver 2 end
    
#    # lkp edit ends
# class StreamConvTranspose2d(nn.Module):
#     def __init__(self, 
#                  in_channels: int,
#                  out_channels: int,
#                  kernel_size: Union[int, Tuple[int, int]],
#                  stride: Union[int, Tuple[int, int]] = 1,
#                  padding: Union[str, int, Tuple[int, int]] = 0,
#                  dilation: Union[int, Tuple[int, int]] = 1,
#                  groups: int = 1,
#                  bias: bool = True,
#                  *args, **kargs):
#         super().__init__(*args, **kargs)
#         """
#         kernel_size = [T_size, F_size] by default
#         stride = [T_stride, F_stride], and T_stride == 1
#         """
#         self.in_channels = in_channels
#         self.out_channels = out_channels
#         if type(kernel_size) is int:
#             self.T_size = kernel_size
#             self.F_size = kernel_size
#         elif type(kernel_size) in [list, tuple]:
#             self.T_size, self.F_size = kernel_size
#         else:
#             raise ValueError('Invalid kernel size.')
            
#         if type(stride) is int:
#             self.T_stride = stride
#             self.F_stride = stride
#         elif type(stride) in [list, tuple]:
#             self.T_stride, self.F_stride = stride
#         else:
#             raise ValueError('Invalid stride size.')
        
#         assert self.T_stride == 1

#         if type(padding) is int:
#             self.T_pad = padding
#             self.F_pad = padding
#         elif type(padding) in [list, tuple]:
#             self.T_pad, self.F_pad = padding
#         else:
#             raise ValueError('Invalid padding size.')
#         assert(self.T_pad == 0) 

#         if type(dilation) is int:
#             self.T_dilation = dilation
#             self.F_dilation = dilation
#         elif type(dilation) in [list, tuple]:
#             self.T_dilation, self.F_dilation = dilation
#         else:
#             raise ValueError('Invalid dilation size.')
        
#         self.groups = groups
#         stride_tuple = (self.T_stride, 1)
#         padding_tuple = (self.T_pad, 0)

#         # --- THE SPLIT-AND-CONCAT BYPASS ---
#         if groups == 1:
#             self.convs = nn.ModuleList([
#                 nn.Conv2d(in_channels, out_channels, kernel_size, 
#                           stride=stride_tuple, padding=padding_tuple, 
#                           dilation=dilation, bias=bias)
#             ])
#         else:
#             assert in_channels % groups == 0
#             assert out_channels % groups == 0
#             in_per_group = in_channels // groups
#             out_per_group = out_channels // groups
            
#             # Create an independent standard Conv2d (groups=1) for EVERY group
#             self.convs = nn.ModuleList([
#                 nn.Conv2d(in_per_group, out_per_group, kernel_size, 
#                           stride=stride_tuple, padding=padding_tuple, 
#                           dilation=dilation, bias=bias)
#                 for _ in range(groups)
#             ])
#     # #lkp edit v4 start: 3d flatten before concat, then 4d before convolution, to bypass TFLite layout optimizer and avoid quantisation issue
    
#     def forward(self, x, cache):
#         B, C_in, _, F_in = x.shape
#         T_cache = cache.shape[2]

#         # 1. THE 3D FLATTEN BYPASS
#         cache_3d = cache.contiguous().view(B, C_in, T_cache * F_in)
#         x_3d = x.contiguous().view(B, C_in, 1 * F_in)
        
#         # 2. Concat safely in 3D
#         inp_3d = torch.cat([cache_3d, x_3d], dim=2)
        
#         # 3. Inflate perfectly back to 4D
#         inp = inp_3d.contiguous().view(B, C_in, T_cache + 1, F_in)

#         out_cache = inp[:, :, 1:, :]
#         bs, C, T, F = inp.shape
        
#         # --- THE REST OF YOUR LOGIC IS UNTOUCHED ---
#         # Upsampling operation
#         if self.F_stride > 1: 
#             inp = torch.cat([inp[:,:,:,:,None], torch.zeros([bs,C,T,F,self.F_stride-1])], dim = -1).reshape([bs,C,T,-1])
#             left_pad = self.F_stride - 1
#             if self.F_size > 1:
#                 if left_pad <= self.F_size - 1:
#                     inp = torch.nn.functional.pad(inp, pad = [(self.F_size - 1)*self.F_dilation-self.F_pad, (self.F_size - 1)*self.F_dilation-self.F_pad - left_pad, 0, 0])
#                 else:
#                     raise(NotImplementedError)
#             else:
#                 raise(NotImplementedError)
#         else: # F_stride = 1
#             inp = torch.nn.functional.pad(inp, pad=[(self.F_size-1)*self.F_dilation-self.F_pad, (self.F_size-1)*self.F_dilation-self.F_pad])
                
#         # --- SPLIT AND CONCAT EXECUTION ---
#         if self.groups == 1:
#             outp = self.convs[0](inp)
#         else:
#             in_chunks = torch.chunk(inp, self.groups, dim=1)
#             out_chunks = []
#             for i in range(self.groups):
#                 out_chunks.append(self.convs[i](in_chunks[i]))
#             outp = torch.cat(out_chunks, dim=1)
    
#         return outp, out_cache

#      #lkp edit v4 end
    
#     #lkp edit ver3 ends
    

if __name__ == '__main__':
    from convert import convert_to_stream

    ### test Conv1d Stream
    Sconv = StreamConv1d(1, 1, 3)
    Conv = nn.Conv1d(1, 1, 3)
    convert_to_stream(Sconv, Conv)

    test_input = torch.randn([1, 1, 10])
    with torch.no_grad():
        ## Non-Streaming
        test_out1 = Conv(torch.nn.functional.pad(test_input, [2,0]))
        
        ## Streaming
        cache = torch.zeros([1, 1, 2])
        test_out2 = []
        for i in range(10):
            out, cache = Sconv(test_input[..., i:i+1], cache)
            test_out2.append(out)
        test_out2 = torch.cat(test_out2, dim=-1)
        print(">>> Streaming Conv1d error:", (test_out1 - test_out2).abs().max())

    ### test Conv2d Stream
    Sconv = StreamConv2d(1, 1, [3,3])
    Conv = nn.Conv2d(1, 1, (3,3))
    convert_to_stream(Sconv, Conv)

    test_input = torch.randn([1,1,10,6])

    with torch.no_grad():
        ## Non-Streaming
        test_out1 = Conv(torch.nn.functional.pad(test_input,[0,0,2,0]))
        
        ## Streaming
        cache = torch.zeros([1,1,2,6])
        test_out2 = []
        for i in range(10):
            out, cache = Sconv(test_input[:,:, i:i+1], cache)
            test_out2.append(out)
        test_out2 = torch.cat(test_out2, dim=2)
        print(">>> Streaming Conv2d error:", (test_out1 - test_out2).abs().max())

        
    ### test ConvTranspose2d Stream
    kt = 3  # kernel size along T axis
    dt = 2  # dilation along T axis
    pt = (kt-1) * dt # padding along T axis
    DeConv = torch.nn.ConvTranspose2d(4, 8, (kt,3), stride=(1,2), padding=(pt,1), dilation=(dt,2), groups=2)
    SDeconv = StreamConvTranspose2d(4, 8, (kt,3), stride=(1,2), padding=(2*2,1), dilation=(dt,2), groups=2)
    convert_to_stream(SDeconv, DeConv)

    test_input = torch.randn([1, 4, 100, 6])
    with torch.no_grad():
        ## Non-Streaming
        test_out1 = DeConv(nn.functional.pad(test_input, [0,0,pt,0]))  # causal padding!
        test_out1 = test_out1
        ## Streaming
        test_out2 = []
        cache = torch.zeros([1, 4, pt, 6])
        for i in range(100):
            out, cache = SDeconv(test_input[:,:, i:i+1], cache)
            test_out2.append(out)
        test_out2 = torch.cat(test_out2, dim=2)

        print(">>> Streaming ConvTranspose2d error:", (test_out1 - test_out2).abs().max())
    

