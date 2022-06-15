"""
    msft_ble_app
    @desc   This python script connects to the msft team esp32 s3 module and 
            receive the button state 

    @issues 1. The write_gatt_char function isn't working as expected yet,
                at the moment  I can't send data to the esp32
                Probable solution: Check another BLE library, Test the bleak library 
                on windows
"""

import asyncio
import platform
import sys
from bleak import BleakScanner, BleakClient

# BLE_NAME = (
#     "Teams mute button"
#     if platform.system() != "Darwin"
#     else "Teams mute button - d"
# )

BLE_NAME = "Teams mute button"
#these are the tx and rx with respect to the ble module of the button 
CHARACTERISTIC_UUID_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


def handle_tx(sender, data):
    print(sender, data)

async def main(ble_nm):
    devices = await BleakScanner.discover()
    # devices = await BleakScanner.find
    print("Finding name: {}, platform: {}".format(ble_nm, platform.system()))
    for device in devices:
        print(device.name)

        if (device.name == ble_nm):
            print("Found teams mute button!!!")   

            async with BleakClient(device) as client:
                # svcs = await client.get_services()
                # print("Services:")
                # for service in svcs:
                #     print(service)
                try:
                    await client.start_notify(CHARACTERISTIC_UUID_TX, handle_tx)
                    await asyncio.sleep(4.0)
                    data_str = "heeloo"
                    data_bytes= bytearray(data_str.encode())

                    # loop = asyncio.get_running_loop()
                    # data_bytes = await loop.run_in_executor(None, sys.stdin.buffer.readline)

                    # data will be empty on EOF (e.g. CTRL+D on *nix)
                    if not data_bytes:
                        return

                    # some devices, like devices running MicroPython, expect Windows
                    # line endings (uncomment line below if needed)
                    # data = data.replace(b"\n", b"\r\n")

                    await client.write_gatt_char(CHARACTERISTIC_UUID_TX, data_bytes)
                    print("sent:", data_bytes)
                    await asyncio.sleep(4.0)
                    # await client.stop_notify(CHARACTERISTIC_UUID_RX)
                except Exception as e:
                    print(e)


if __name__ == "__main__":
    #pass in the user defined ble name or the default
    asyncio.run(main(sys.argv[1] if len(sys.argv) == 2 else BLE_NAME))


