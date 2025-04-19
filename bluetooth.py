# Pi Zero Script (Python 3)
import asyncio
from bleak import BleakClient ,BleakScanner
import time
import struct
import bluetooth

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




# Replace these with your Pico's details

SERVICE_UUID = UUID(0x180A)   # Service UUID on Pico
TEMP_CHAR_UUID = UUID(0x2A29)  # Temperature characteristic UUID

def _decode_temperature(data):
    """Decode temperature from sint16 format (hundredths of a degree)."""
    return struct.unpack("<h", data)[0] / 100

async def main():
    try:
        async with BleakClient(PICO_ADDRESS) as client:
            print(f"Connected to Pico at {PICO_ADDRESS}")

            while True:
                # Read temperature characteristic directly
                data = await client.read_gatt_char(TEMP_CHAR_UUID)
                temp_deg_c = _decode_temperature(data)
                print(f"Temperature: {temp_deg_c:.2f}°C")
                await asyncio.sleep(1)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())