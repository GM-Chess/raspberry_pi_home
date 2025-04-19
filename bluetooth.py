# Pi Zero Script (Python 3)
import asyncio
from bleak import BleakClient
from machine import Pin, I2C
import time
import network 
import socket

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
        # Write to the characteristic
        await client.write_gatt_char("00002a29-0000-1000-8000-00805f9b34fb", b"Hello from Pi Zero!")
        print("Sent: Hello from Pi Zero!")
        # Wait for a while to see the response
        await asyncio.sleep(1)
        
if __name__ == "__main__":
	while True:
		asyncio.run(main())
