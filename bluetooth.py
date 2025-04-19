# Pi Zero Script (Python 3)
import asyncio
from bleak import BleakClient

# Replace with your Pico's BLE MAC
PICO_ADDRESS = "2C:CF:67:C9:C3:66"  # Use colons, not underscores
PICO_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
async def main():
    async with BleakClient(PICO_ADDRESS) as client:
        # Verify connection
        if not client.is_connected:
            await client.connect()

        # Read the characteristic
        value = await client.read_gatt_char("00002a29-0000-1000-8000-00805f9b34fb")
        print("Received:", value.decode())
if __name__ == "__main__":
	while True:
		asyncio.run(main())
