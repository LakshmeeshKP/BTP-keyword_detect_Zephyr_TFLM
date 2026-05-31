Notes:
- The above folder contains the updated prj.conf used to make overclocking work in the [STFT](https://github.com/LakshmeeshKP/BTP-keyword_detect_Zephyr_TFLM/tree/main/BTP-1/Codes/STFT_using_KissFFT) application.
- I also tried to modify the vreg to support higher rates, However, the overlay file did not change the regulator voltage. I am not sure if it is not supported yet, or if what I tried was incomplete.

-----------------

- One way to overcome timing related constraint is to speed-up the microcontroller clock, to meet small improvements in deadlines.<br>
- The default clock-rate for pico is 133MHz. I overclocked it to 250MHz, approximately doubling the computation speed, and making it feasible to make the keyword detection application real-time.<br>
- We may also need to correspondingly increase the core voltage for stability. However, the overlay approach did not change the voltage regulator state for me.<br>
A non-portable workaround is by using vreg_set_voltage() from picoSDK, if necessary.

---

## Implementation

### Enabling overclocking in Zephyr
- update CONFIG_SYS_CLOCK_HW_CYCLES_PER_SEC=<int> to your desired rate.
- default for pico is 133000000 (133MHz). 

### Voltage considerations
- Higher clock-rate may require a corresponding increase in core voltage.
- We can get stable overclock upto 250-270 at default voltage and upto 360MHz by increasing core voltage.

--- 

## Test results

- Done using the stft application
- The time taken to take stft for 16k samples (256 window, 128 step) was observed at two clock rates

| Clock Rate | Execution Time |
| :--- | :--- |
| **133 MHz** (Default) | 0.979 seconds |
| **250 MHz** (Overclocked) | 0.489 seconds |

- A 2x improvement is observed from 1.88x increase in clock rate
