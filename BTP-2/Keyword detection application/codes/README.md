build and test commands:

(activate the zephyr environment)<br>
zephyrproject\.venv\Scripts\activate.bat<br>
cd C:\Users\laksh\zephyrproject\zephyr<br>

(src folder location: zephyrproject/zephyr/applications/final/src)<br>
(overlay for ADC, and cdc-acm-conole snippet included at build)<br>
west build -p always -b rpi_pico_rp2040_w -S cdc-acm-console applications/final -- -DDTC_OVERLAY_FILE=mic_pico_w.overlay

(view serial output using pyserial)<br>
python -m serial.tools.miniterm "COM4" 115200



