# Pi Zero Script (Python 3)
import asyncio
import struct
from bleak import BleakClient

# PICO'S ADDRESS AND UUIDs (MUST MATCH PICO'S CODE)
PICO_ADDRESS = "2C:CF:67:C9:C3:66"  # Your Pico's MAC address
SERVICE_UUID = "0000181a-0000-1000-8000-00805f9b34fb"  # Environmental Sensing Service
TEMP_CHAR_UUID = "00002a6e-0000-1000-8000-00805f9b34fb"  # Temperature Characteristic
LED_CONTROL_UUID = "932c32bd-0004-47a2-835a-a8d455b859dd"  # Custom LED UUID (MUST MATCH PICO)

def _decode_temperature(data):
    """Decode temperature from sint16 format (hundredths of a degree)."""
    return struct.unpack("<h", data)[0] / 100

async def main():
    try:
        async with BleakClient(PICO_ADDRESS) as client:
            print(f"Connected to Pico at {PICO_ADDRESS}")

            while True:
                # Read temperature
                temp_data = await client.read_gatt_char(TEMP_CHAR_UUID)
                temp_deg_c = _decode_temperature(temp_data)
                print(f"Temperature: {temp_deg_c:.2f}°C")

                # Control LED (example: toggle)
                await client.write_gatt_char(LED_CONTROL_UUID, b"\x01")  # Turn ON
                print("LED turned ON")
                await asyncio.sleep(1)
                await client.write_gatt_char(LED_CONTROL_UUID, b"\x00")  # Turn OFF
                print("LED turned OFF")
                
                await asyncio.sleep(2)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())