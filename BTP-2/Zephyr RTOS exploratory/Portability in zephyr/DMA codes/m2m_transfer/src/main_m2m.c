#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/dma.h>
#include <zephyr/drivers/timer/system_timer.h>
#include <zephyr/sys/clock.h>
#include <zephyr/sys/time_units.h>

#define BUF_SIZE 10

__aligned(32) uint32_t src[BUF_SIZE];
__aligned(32) uint32_t dst[BUF_SIZE];

int main(void){
    for (int i = 0; i < BUF_SIZE; i++) {
        src[i] = 0xABCDABCD;
    }
    
    const struct device *dma_dev = DEVICE_DT_GET(DT_NODELABEL(dma));
    
    if(!device_is_ready(dma_dev)) {
        printk("DMA not ready\n");
        while(1){};
    }
    
    struct dma_block_config blk = {0};
    blk.source_address = (uint32_t)src;
    blk.dest_address   = (uint32_t)dst;
    blk.block_size     = sizeof(src);
    
    struct dma_config cfg = {0};
    cfg.channel_direction = MEMORY_TO_MEMORY;
    cfg.source_data_size = sizeof(uint32_t);
    cfg.dest_data_size = sizeof(uint32_t);
    cfg.block_count = 1;
    cfg.head_block = &blk;

    dma_config(dma_dev, 0, &cfg);
    dma_start(dma_dev, 0);

    k_msleep(10);

    for (int i = 0; i < BUF_SIZE; i++) {
        printk("dst[%d] = 0x%X\n", i, dst[i]);
    }
}