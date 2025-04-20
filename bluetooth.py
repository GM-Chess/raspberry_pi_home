# Pi Zero Script (Python 3)
import asyncio
import struct
from bleak import BleakClient
# import network
# import socket
# import time

# # WiFi credentials
# ssid = 'hello world'
# password = 'guinessWorldRecord'

# # Connect to WiFi
# wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# wlan.connect(ssid, password)

# max_wait = 10
# while max_wait > 0:
#     if wlan.status() < 0 or wlan.status() >= 3:
#         break
#     max_wait -= 1
#     print('waiting for connection...')
#     time.sleep(1)

# if wlan.status() != 3:
#     raise RuntimeError('network connection failed')
# else:
#     print('connected')
#     status = wlan.ifconfig()
#     print('ip:', status[0])

# # Create socket
# addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
# s = socket.socket()
# s.bind(addr)
# s.listen(1)
# print('listening on', addr)

# # HTML and CSS
# html_template = """<!DOCTYPE html>
# <html>
# <head>
#     <title>Home Control webpage</title>
#     <meta http-equiv="refresh" content="5">
#     <style>
#         body { font-family: Arial, sans-serif; text-align: center; margin: 40px; }
#         .sensor-data { font-size: 24px; margin: 20px; }
#         button { 
#             padding: 15px 30px; 
#             font-size: 18px; 
#             margin: 10px; 
#             border: none; 
#             border-radius: 5px; 
#             cursor: pointer; 
#         }
#         .pump-in { background-color: #4CAF50; color: white; }
#         .pump-out { background-color: #f44336; color: white; }
#         .status { margin-top: 20px; }
#     </style>
#     <script>
#         function controlPump(pump, action) {
#             fetch(`/${pump}/${action}`)
#                 .then(response => {
#                     updateButtonStates();
#                 });
#         }

#         function updateButtonStates() {
#             fetch('/status')
#                 .then(response => response.json())
#                 .then(data => {
#                     document.getElementById('pump-in-state').textContent = data.pump_in ? 'ON' : 'OFF';
#                     document.getElementById('pump-out-state').textContent = data.pump_out ? 'ON' : 'OFF';
#                 });
#         }

#         setInterval(updateButtonStates, 1000);
#     </script>
# </head>
# <body>
#     <h1>Home Control webpage</h1>
    
#     <div class="sensor-data">
#         <h2>Temperature: %.1f&#176;C</h2>
#         <h2>Humidity: %.1f%%</h2>
#     </div>

#     <div class="controls">
#         <button class="pump-in" onclick="controlPump('pump_in', 'on')">Pump In ON</button>
#         <button class="pump-in" onclick="controlPump('pump_in', 'off')">Pump In OFF</button>
#         <br>
#         <button class="pump-out" onclick="controlPump('pump_out', 'on')">Pump Out ON</button>
#         <button class="pump-out" onclick="controlPump('pump_out', 'off')">Pump Out OFF</button>
#     </div>

#     <div class="status">
#         <p>Pump In Status: <span id="pump-in-state">%s</span></p>
#         <p>Pump Out Status: <span id="pump-out-state">%s</span></p>
#     </div>
# </body>
# </html>
# """


# PICO'S ADDRESS AND UUIDs (MUST MATCH PICO'S CODE)
PICO_ADDRESS = "2C:CF:67:C9:C3:66"  # Your Pico's MAC address
SERVICE_UUID = "932c32bd-0000-47a2-835a-a8d455b859dd"  # Environmental Sensing Service
TEMP_CHAR_UUID = "932c32bd-0001-47a2-835a-a8d455b859dd"  # Temperature Characteristic
LED_CONTROL_UUID = "932c32bd-0004-47a2-835a-a8d455b859dd"  # Custom LED UUID (MUST MATCH PICO)

def _decode_temperature(data):
    """Decode temperature from sint16 format (hundredths of a degree)."""
    return struct.unpack("<h", data)[4] / 100

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