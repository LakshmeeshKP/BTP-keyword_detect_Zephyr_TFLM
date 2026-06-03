import serial
import numpy as np
from scipy.io.wavfile import write
import threading
import time
from datetime import datetime

# --- CONFIGURATION ---
CMD_PORT = 'COM3'   # The port that receives Zephyr Shell commands
DATA_PORT = 'COM4'  # The port that outputs binary audio
# BAUD_RATE = 115200
BAUD_RATE = 460800 # min (16000*16)*(10/8) = 320000 bps . next standard rate taken
testing=False 
# ---------------------

print("Connecting to Pico...")

try:
    cmd_ser = serial.Serial(CMD_PORT, BAUD_RATE, timeout=1)
    cmd_ser.setDTR(True) 
    
    data_ser = serial.Serial(DATA_PORT, BAUD_RATE)
    data_ser.setDTR(True)
    
    print(f"Connected! Commands mapped to {CMD_PORT}, Data mapped to {DATA_PORT}.")
except Exception as e:
    print(f"Connection failed: {e}")
    exit()

raw_data = bytearray()
recording = False

def listen_for_audio():
    global raw_data, recording
    while True:
        # print("active")
        if(testing):
            # print("Testing mode...")
            if data_ser.in_waiting > 0:
                test_bytes = data_ser.read(data_ser.in_waiting)
                print(f"TEST READ: {len(test_bytes)} bytes: {test_bytes}")
        else:

            if recording and data_ser.in_waiting > 0:
                raw_data.extend(data_ser.read(data_ser.in_waiting))
        time.sleep(1) # Prevent 100% CPU usage


# This lets you see printk() messages from the Pico!
def listen_to_pico_logs():
    while True:
        # print("Listening for Pico logs...")
        if cmd_ser.in_waiting > 0:
            try:
                log = cmd_ser.readline().decode('utf-8', errors='ignore').strip()
                if log: 
                    print(f"[PICO LOG]: {log}")
            except:
                pass
        time.sleep(0.01)

# threading.Thread(target=listen_to_pico_logs, daemon=True).start()
threading.Thread(target=listen_for_audio, daemon=True).start()

while True:
    try:
        cmd = input("\nEnter command (start / stop / exit): ").strip().lower()

        if cmd == "start":
            data_ser.reset_input_buffer()
            raw_data.clear()
            recording = True
            cmd_ser.write(b'start\r\n')
            print("Recording started. Listening for audio...")

        elif cmd == "stop":
            cmd_ser.write(b'stop\r\n')
            time.sleep(0.1) 
            recording = False
            
            print(f"Recording stopped. Captured {len(raw_data)} bytes.")

            if len(raw_data) > 0:
                valid_bytes = len(raw_data) - (len(raw_data) % 2)
                arr = np.frombuffer(raw_data[:valid_bytes], dtype=np.uint16).astype(np.int32)
                actual_center = np.mean(arr)
                print(f"DEBUG: Center detected at {actual_center:.1f}")
                arr=((arr- actual_center) *16) #for 12 bit adc #centre and stretch to 16 bit range
                arr = np.clip(arr, -32768, 32767)
                arr = arr.astype(np.int16)
                timestamp = datetime.now().strftime("%H%M%S")
                filename = f"zephyr/applications/dma_test/audio_{timestamp}.wav"
                
                write(filename, 16000, arr)
                # write(filename, 4000, arr)
                print(f"Saved as: {filename} ({len(arr)} samples)")
            else:
                print("No data was captured.")

        elif cmd == "exit":
            print("Exiting...")
            break

        elif cmd == "test_usb":
            print("Running test...")
            data_ser.reset_input_buffer()
            raw_data.clear()
            recording = True
            cmd_ser.write(b'test_usb\r\n')
            print("Recording started. Listening for audio...")

        else:
            print("Invalid command. Please type 'start', 'stop', or 'exit'")

    except KeyboardInterrupt:
        break

cmd_ser.close()
data_ser.close()
print("Ports closed.")