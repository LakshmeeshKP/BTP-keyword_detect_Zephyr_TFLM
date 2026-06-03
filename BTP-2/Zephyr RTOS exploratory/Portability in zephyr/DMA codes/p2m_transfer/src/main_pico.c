#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/dma.h>
#include "hardware/adc.h"

uint16_t buffer[256];
static struct dma_config dma_cfg = {0};
static struct dma_block_config block_cfg = {0};

void dma_callback(const struct device *dev, void *user_data, uint32_t channel, int status){
    if (status < 0) {
        printk("DMA error\n");
        return;
    }
    printk("DMA block complete\n");
}


int main(void){

    k_msleep(5000); //wait for usb

    printf("initial buffer:\n");
    for(int i = 0; i < 256; i++){
        printf("%d ", buffer[i]);
    }
    
    static const struct device *dma_dev = DEVICE_DT_GET(DT_NODELABEL(dma));
    if (!device_is_ready(dma_dev)) {
        printk("DMA not ready\n");
    }
    printk("DMA ready\n");
    
    //configuring 
    block_cfg.source_address = 0x4004C00C; //ADC FIFO address
    block_cfg.dest_address   = (uint32_t)buffer;
    block_cfg.block_size     = sizeof(buffer);
    block_cfg.source_addr_adj = DMA_ADDR_ADJ_NO_CHANGE;
    block_cfg.dest_addr_adj   = DMA_ADDR_ADJ_INCREMENT;
    
    dma_cfg.channel_direction = PERIPHERAL_TO_MEMORY;
    dma_cfg.source_data_size  = 2;
    dma_cfg.dest_data_size    = 2;
    dma_cfg.block_count       = 1;
    dma_cfg.head_block        = &block_cfg;
    dma_cfg.dma_slot          = 0x0b; //related to dreq
    // dma_cfg.dma_slot          = RPI_PICO_DMA_SLOT_ADC;
    dma_cfg.dma_callback      = dma_callback;
    
    adc_init();
    adc_gpio_init(26); //adc0=gpio26
    adc_select_input(0); //channel 0
    adc_fifo_setup(true,true, 1,false,false);
    adc_set_clkdiv(31.25); // 48000000/(96*16000) //see pg599 of rp2040 datasheet
    adc_run(true);

    int ch = 0;
    dma_config(dma_dev, ch, &dma_cfg);
    dma_start(dma_dev, ch);

    printf("buffer finally:\n");
    
    while(1){
        for(int i = 0; i < 256; i++){
            printf("%d ", buffer[i]);
        }
        k_msleep(1000);
    }
}

