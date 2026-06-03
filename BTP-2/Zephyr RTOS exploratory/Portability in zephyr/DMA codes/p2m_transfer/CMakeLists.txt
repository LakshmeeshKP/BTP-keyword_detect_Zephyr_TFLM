# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(dma_test)

target_include_directories(app PRIVATE
    ${ZEPHYR_BASE}/../modules/hal/rpi_pico/src/rp2_common/hardware_adc/include
)

file(GLOB app_sources src/*)
target_sources(app PRIVATE 
    ${app_sources}
    )
