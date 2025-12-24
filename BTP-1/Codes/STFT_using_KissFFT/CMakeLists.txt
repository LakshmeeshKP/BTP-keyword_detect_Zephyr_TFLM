# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(stft)

zephyr_include_directories(
  ${ZEPHYR_BASE}/../optional/modules/lib/tflite-micro/third_party_static/kissfft
)

file(GLOB app_sources src/*)
target_sources(app PRIVATE 
    ${app_sources}
    ${ZEPHYR_BASE}/../optional/modules/lib/tflite-micro/third_party_static/kissfft/kiss_fft.c
    ${ZEPHYR_BASE}/../optional/modules/lib/tflite-micro/third_party_static/kissfft/tools/kiss_fftr.c
)
