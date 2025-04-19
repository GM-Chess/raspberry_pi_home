# Pi Zero Script (Python 3)
import asyncio
from bleak import BleakClient ,BleakScanner
import time
import struct

# Replace with your Pico's BLE MAC
PICO_ADDRESS = "2C:CF:67:C9:C3:66"  # Use colons, not underscores
PICO_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
# async def main():
#     async with BleakClient(PICO_ADDRESS) as client:
#         # Verify connection
#         if not client.is_connected:
#             await client.connect()

#         # Read the characteristic
#         value = await client.read_gatt_char("00002a29-0000-1000-8000-00805f9b34fb")
#         print("Received:", value.decode())
#         # Write to the characteristic
#         await client.write_gatt_char("00002a29-0000-1000-8000-00805f9b34fb", b"Hello from Pi Zero!")
#         print("Sent: Hello from Pi Zero!")
#         # Wait for a while to see the response
#         await asyncio.sleep(1)

# if __name__ == "__main__":
# 	while True:
# 		asyncio.run(main())


# UUIDs for Environmental Sensing Service and Temperature Characteristic
_ENV_SENSE_UUID = "0000181a-0000-1000-8000-00805f9b34fb"
_ENV_SENSE_TEMP_UUID = "00002a6e-0000-1000-8000-00805f9b34fb"

def _decode_temperature(data):
    """Decode temperature from sint16 format (hundredths of a degree)."""
    return struct.unpack("<h", data)[0] / 100

async def find_temp_sensor():
    """Scan for the temperature sensor device."""
    # Scan for devices with the Environmental Sensing service and correct name
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: ad.local_name == "mpy-temp" and _ENV_SENSE_UUID in ad.service_uuids,
        timeout=5.0  # Scan for 5 seconds to match original code
    )
    return device

async def main():
    device = await find_temp_sensor()
    if not device:
        print("Temperature sensor not found")
        return

    try:
        async with BleakClient(device) as client:
            print(f"Connected to {device.name}")

            while True:
                # Read temperature characteristic
                data = await client.read_gatt_char(_ENV_SENSE_TEMP_UUID)
                temp_deg_c = _decode_temperature(data)
                print(f"Temperature: {temp_deg_c:.2f}°C")
                await asyncio.sleep(1)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())