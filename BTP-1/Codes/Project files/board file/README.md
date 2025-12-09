Add the above folder under boards/raspberrypi , as it is also dependent on other common board files as well. 

The changes required to make the board file work were:
- add KConfig definition for "BOARD_RPI_PICO_RP2040_W" 
- add CONFIG_CYW43439=y in "rpi_pico_rp2040_w_defconfig"
- add "if BOARD_RPI_PICO_RP2040_W && WIFI_AIROC" in "kconfig.defconfig"
- modify board config name in "Kconfig.rpi_pico_rp2040_w"
- Rename the original kconfig file to "Kconfig.rpi_pico_rp2040_w"


