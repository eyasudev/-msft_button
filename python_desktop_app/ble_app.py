"""
    msft_ble_app
    @desc   This python script connects to the msft team esp32 s3 module and 
            receive the button state 

    @issues 1. The write_gatt_char function isn't working as expected yet,
                at the moment  I can't send data to the esp32
                Probable solution: Check another BLE library for python, or Test the bleak library 
                on windows
"""

import asyncio
import platform
import sys
import threading
import time

from bleak import BleakScanner, BleakClient
#https://bleak.readthedocs.io/en/latest/usage.html


BLE_NAME = "Teams mute button"
#these are the tx and rx with respect to the ble module of the button 
#i.e. tx channel would the tx from the esp32 and rx to the PC 
CHARACTERISTIC_UUID_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


#global variables for internal use
count_time = 0
NO_RESPONSE_TIMEOUT = 3 #3 secs
#low value is good, counter only starts after establishing connection

BTN_PRESSED = True
BTN_RELEASED = False

#global variables for the external use
button_state = BTN_RELEASED

def isBleAlive():
    global count_time
    global NO_RESPONSE_TIMEOUT
    return (count_time < NO_RESPONSE_TIMEOUT)
    

def handle_tx(sender, data):
    global button_state 
    global count_time

    # button_state = True if (data == b'teamsbtn:01') else False
    if (data == b'teamsbtn:01'):
        button_state = True
    elif (data == b'teamsbtn:00'):
        button_state = False
    #don't assign value if incoming data isn't recognisable
    
    count_time = 0
    # print(sender, data, button_state)

async def find_device(ble_nm):
    global count_time
    global NO_RESPONSE_TIMEOUT
    
    devices = await BleakScanner.discover()

    print("Finding name: {}, platform: {}".format(ble_nm, platform.system()))
    for device in devices:
        print(device.name)

        if (device.name == ble_nm):
            print("Found teams mute button!!!")   
            
            async with BleakClient(device) as client:
                try:
                    await client.start_notify(CHARACTERISTIC_UUID_TX, handle_tx)
                    count_time = 0
                    #while response is being received from ble module count_time is increased
                    while True: 
                        count_time = count_time + 1
                        # print("ble thread, cnt: {}".format(count_time))
                        if count_time > NO_RESPONSE_TIMEOUT:
                            return
                        await asyncio.sleep(1)

                except Exception as e:
                    print(e)
    
async def ble_start(ble_nm):
    while True:
        await find_device(ble_nm)



def main():
    #pass in the user defined ble name or the default
    # asyncio.run(ble_start(sys.argv[1] if len(sys.argv) == 2 else BLE_NAME))
    asyncio.run(ble_start(BLE_NAME))    

if __name__ == "__main__":
    main()
    




