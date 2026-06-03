#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/dma.h>
#include "hardware/adc.h"
#include <zephyr/shell/shell.h>
#include <zephyr/drivers/uart.h>
#include <stdint.h>

volatile bool record = false;

// test codes region start
#define TEST_USB_STREAMING 1

#if TEST_USB_STREAMING
    bool test_send = false;
    static int test_usb_cmd(const struct shell *shell, size_t argc, char **argv){
        ARG_UNUSED(argc);
        ARG_UNUSED(argv); 
        ARG_UNUSED(shell); 
        printk("started test USB streaming (no adc or DMA used)\n");
        test_send=true;
        return 0;
    }
    uint16_t test_buffer[5]={1,2,3,4,5};

    #define SINE_WAVE_1KHZ \
        2048, 2813, 3462, 3896, 4048, 3896, 3462, 2813, \
        2048, 1283,  634,  200,   48,  200,  634, 1283
    
        uint16_t buffer_a_sine[256] = {
            SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ,
            SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ,
            SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ,
            SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ
        };
    
        uint16_t buffer_b_sine[256] = {
            SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ,
            SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ,
            SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ,
            SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ, SINE_WAVE_1KHZ
        };

        static int cmd_start(const struct shell *shell, size_t argc, char **argv){
            ARG_UNUSED(argc);
            ARG_UNUSED(argv);
            ARG_UNUSED(shell);
            printk("Recording started\n");
            record = true;
            return 0;
        }
        static int cmd_stop(const struct shell *shell, size_t argc, char **argv){
            ARG_UNUSED(argc);
            ARG_UNUSED(argv); 
            ARG_UNUSED(shell); 
            printk("Recording stopped\n");
            record = false;
            return 0;
        }
#endif

// test codes region end


#if !TEST_USB_STREAMING
uint16_t buffer_a[256];
uint16_t buffer_b[256];
static const struct device *dma_dev;
static struct dma_config dma_cfg = {0};
static struct dma_block_config block_a_cfg = {0};
static struct dma_block_config block_b_cfg = {0};
int dma_channel=0;

volatile bool buffer_a_filled = false;
volatile bool buffer_a_ready = false;
volatile bool buffer_b_ready = false;


void dma_callback(const struct device *dev, void *user_data, uint32_t channel, int status){
    printk("DMA callbacked\n");
    if (status < 0) {
        printk("DMA error\n");
        return;
    }
    // printk("DMA block complete\n");
    
    if(!buffer_a_filled){
        printk("Buffer A filled\n");
        buffer_a_ready = true;
        buffer_b_ready = false;
        buffer_a_filled = true;
    }
    else{
        printk("Buffer B filled\n");
        buffer_a_ready = false;
        buffer_b_ready = true;
        buffer_a_filled = false;
    }
}

void dma_callback2(const struct device *dev, void *user_data, uint32_t channel, int status){
    if (status < 0) {
        printk("DMA error\n");
        return;
    }
    
    // If the user told us to stop, do NOT reload the DMA. Just exit.
    if (!record) {
        return;
    }

    if(!buffer_a_filled){
        printk("Buffer A filled\n");
        // We just filled Buffer A. 
        // Instantly reload DMA to aim at Buffer B and restart.
        dma_reload(dev, channel, 0x4004C00C, (uint32_t)buffer_b, sizeof(buffer_b));
        dma_start(dev, channel);
        
        // Tell the main loop to send Buffer A over USB
        buffer_a_ready = true;
        buffer_b_ready = false;
        buffer_a_filled = true;
    }
    else {
        printk("Buffer B filled\n");
        // We just filled Buffer B. 
        // Instantly reload DMA to aim at Buffer A and restart.
        dma_reload(dev, channel, 0x4004C00C, (uint32_t)buffer_a, sizeof(buffer_a));
        dma_start(dev, channel);

        // Tell the main loop to send Buffer B over USB
        buffer_a_ready = false;
        buffer_b_ready = true;
        buffer_a_filled = false;
    }
}

static int cmd_start(const struct shell *shell, size_t argc, char **argv){
    ARG_UNUSED(argc);
    ARG_UNUSED(argv);
    ARG_UNUSED(shell);
    // shell_print(shell, "Recording started");
    printk("Recording started\n");
    record = true;
    dma_setup2();
    dma_start(dma_dev, dma_channel);
    adc_run(true);
    return 0;
}
static int cmd_stop(const struct shell *shell, size_t argc, char **argv){
    ARG_UNUSED(argc);
    ARG_UNUSED(argv); 
    ARG_UNUSED(shell); 
    // shell_print(shell, "Recording stopped");
    printk("Recording stopped\n");
    adc_run(false);
    dma_stop(dma_dev, dma_channel);

    record = false;
    buffer_a_filled = false;
    buffer_a_ready = false;
    buffer_b_ready = false;

    return 0;
}
void adc_setup();
void dma_setup();
void dma_setup2();
#endif

void usb_send(const struct device *dev, uint8_t *data, size_t len);

const struct device *usb_printk;
const struct device *usb_data;


int main(void){
    k_msleep(5000); //wait for usb

    usb_printk = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));
    if (!device_is_ready(usb_printk)) {
        printk("USB printk not ready\n");
    }
    printk("USB printk ready\n");
    usb_data = DEVICE_DT_GET(DT_NODELABEL(cdc_acm_lkp));
    if (!device_is_ready(usb_data)) {
        printk("USB data UART not ready\n");
    }
    printk("USB data ready\n");
    #if !TEST_USB_STREAMING         
            dma_dev = DEVICE_DT_GET(DT_NODELABEL(dma));
            if (!device_is_ready(dma_dev)) {
                printk("DMA not ready\n");
            }
            printk("DMA ready\n");
            
            // dma_setup();
            dma_setup2();
            adc_setup();
            printk("Setup complete\n");
    #else
        printk("Test USB streaming mode enabled. No ADC or DMA will be used.\n");
    #endif
    SHELL_CMD_REGISTER(start, NULL, "Start recording", cmd_start);
    SHELL_CMD_REGISTER(stop, NULL, "Stop recording", cmd_stop);
    SHELL_CMD_REGISTER(test_usb, NULL, "Test usb streaming", test_usb_cmd);

    printk("shell cmds registerd\n");


    while(1){
            #if !TEST_USB_STREAMING
            if (buffer_a_ready){
                printk("Sending buffer A\n");
                // usb_send(usb_data, (uint8_t *)buffer_a, sizeof(buffer_a));
                usb_send(usb_data, (uint8_t *)buffer_a_sine, sizeof(buffer_a_sine));
                buffer_a_ready = false;
            }
            else if (buffer_b_ready){
                printk("Sending buffer B\n");
                // usb_send(usb_data, (uint8_t *)buffer_b, sizeof(buffer_b));
                usb_send(usb_data, (uint8_t *)buffer_b_sine, sizeof(buffer_b_sine));
                buffer_b_ready = false;
            }
            k_msleep(100);
            #else
            if (test_send){
            usb_send(usb_data, (uint8_t *)test_buffer, sizeof(test_buffer));
            printk("test buffer sent\n");
            test_send=false;
            }
            else if (record){
                usb_send(usb_data, (uint8_t *)buffer_a_sine, sizeof(buffer_a_sine));
                
                // 256 samples at 16kHz takes exactly 16ms. 
                // We sleep to mimic the hardware ADC filling the next buffer.
                k_msleep(16); 
                
                usb_send(usb_data, (uint8_t *)buffer_b_sine, sizeof(buffer_b_sine));
                k_msleep(16);
            }
            else k_msleep(100);
            #endif
    }
}

#if !TEST_USB_STREAMING
void adc_setup(){
    adc_init();
    adc_gpio_init(26); //adc0=gpio26
    adc_select_input(0); //channel 0
    adc_fifo_setup(true,true, 1,false,false);
    // adc_set_clkdiv(31.25); // 48000000/(96*16000) //see pg599 of rp2040 datasheet
    // adc_set_clkdiv(125); //4khz sampling
    adc_set_clkdiv(3000); // 48000000/(16000) 
    // adc_set_clkdiv(12000); //4khz sampling  //48000000/target_freq
}

// void dma_setup(){
//     buffer_a_ready = false;

//     block_a_cfg.source_address = 0x4004C00C; //ADC FIFO address
//     block_a_cfg.dest_address   = (uint32_t)buffer_a;
//     block_a_cfg.block_size     = sizeof(buffer_a);
//     block_a_cfg.source_addr_adj = DMA_ADDR_ADJ_NO_CHANGE;
//     block_a_cfg.dest_addr_adj   = DMA_ADDR_ADJ_INCREMENT;
//     block_a_cfg.next_block = &block_b_cfg;
    
//     block_b_cfg.source_address = 0x4004C00C; //ADC FIFO address
//     block_b_cfg.dest_address   = (uint32_t)buffer_b;
//     block_b_cfg.block_size     = sizeof(buffer_b);
//     block_b_cfg.source_addr_adj = DMA_ADDR_ADJ_NO_CHANGE;
//     block_b_cfg.dest_addr_adj   = DMA_ADDR_ADJ_INCREMENT;
//     block_b_cfg.next_block = &block_a_cfg;

//     dma_cfg.channel_direction = PERIPHERAL_TO_MEMORY;
//     dma_cfg.source_data_size  = 2;
//     dma_cfg.dest_data_size    = 2;
//     dma_cfg.block_count       = 2;
//     dma_cfg.head_block        = &block_a_cfg;
//     dma_cfg.dma_slot          = 0x0b; //related to dreq
//     // dma_cfg.dma_slot          = RPI_PICO_DMA_SLOT_ADC;
//     dma_cfg.dma_callback      = dma_callback;
//     dma_cfg.complete_callback_en = 1; //fires callback after each block

//     int ret=dma_config(dma_dev, dma_channel, &dma_cfg);
//     if (ret != 0) {
//         printk("\x1b[31mDMA config failed\x1b[0m\n");
//     }
// }

void dma_setup2(){
    buffer_a_ready = false;

    block_a_cfg.source_address = 0x4004C00C; // ADC FIFO address
    block_a_cfg.dest_address   = (uint32_t)buffer_a;
    block_a_cfg.block_size     = sizeof(buffer_a);
    block_a_cfg.source_addr_adj = DMA_ADDR_ADJ_NO_CHANGE;
    block_a_cfg.dest_addr_adj   = DMA_ADDR_ADJ_INCREMENT;
    block_a_cfg.next_block = NULL; 

    dma_cfg.channel_direction = PERIPHERAL_TO_MEMORY;
    dma_cfg.source_data_size  = 2;
    dma_cfg.dest_data_size    = 2;
    dma_cfg.block_count       = 1; 
    dma_cfg.head_block        = &block_a_cfg;
    dma_cfg.dma_slot          = 0x0b; 
    dma_cfg.dma_callback      = dma_callback2;

    int ret = dma_config(dma_dev, dma_channel, &dma_cfg);
    if (ret != 0) {
        printk("\x1b[31mDMA config failed with code: %d\x1b[0m\n", ret);
    } else {
        printk("DMA Configured Successfully.\n");
    }
}
#endif

// void usb_send(const struct device *dev, uint8_t *data, size_t len){
//     //since different hardware has different fifo lengths, we need to test the return value
//     //and continue sending until all samples are sent
//     int sent = 0;
//     while (sent < len) {
//         int ret = uart_fifo_fill(dev, data + sent, len - sent);
//         sent += ret;
//     }
// }

void usb_send(const struct device *dev, uint8_t *data, size_t len){
    for (size_t i = 0; i < len; i++) {
        uart_poll_out(dev, data[i]);
    }
}
