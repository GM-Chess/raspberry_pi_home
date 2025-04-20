# Pi Zero Script (Python 3)
import asyncio
import struct
from bleak import BleakClient
import time
import time
import http.server
import socketserver
import json
import time
from aiohttp import web
import json

PORT = 8080
pump_in = False
pump_out = False



# PICO'S ADDRESS AND UUIDs (MUST MATCH PICO'S CODE)
PICO_ADDRESS = "2C:CF:67:C9:C3:66"  # Your Pico's MAC address
SERVICE_UUID = "932c32bd-0000-47a2-835a-a8d455b859dd"  # Environmental Sensing Service
TEMP_CHAR_UUID = "932c32bd-0001-47a2-835a-a8d455b859dd"  # Temperature Characteristic
HUMIDITY_CHAR_UUID = "932c32bd-0002-47a2-835a-a8d455b859dd"
LED_CONTROL_UUID = "932c32bd-0004-47a2-835a-a8d455b859dd"  # Custom LED UUID (MUST MATCH PICO)
WATER_BIRDS_UUID = "932c32bd-0005-47a2-835a-a8d455b859dd"
FEED_BIRDS_UUID = "932c32bd-0006-47a2-835a-a8d455b859dd"

def _decode_temperature(data):
    """Decode temperature from sint16 format (hundredths of a degree)."""
    return struct.unpack("<h", data)[0] / 100

def _decode_time(data):
    """Decode time from 8-byte format (seconds since epoch * 10^7)."""
    try:
        if len(data) != 8:  # Ensure 8 bytes are received
            print(f"Invalid data length: {len(data)} bytes (expected 8)")
            return None
        time_in_ticks = struct.unpack("<q", data)[0]  # Unpack 8-byte integer
        time_in_seconds = time_in_ticks / 10_000_000  # Convert back to seconds
        converted_time = time.strftime(
            "%a, %d %b %Y %H:%M:%S", time.gmtime(time_in_seconds - 14400)
        )
        return converted_time
    except Exception as e:
        print(f"Error decoding time: {e}")
        return None
    
async def BLE_task():
    try:
        async with BleakClient(PICO_ADDRESS) as client:
            print(f"Connected to Pico at {PICO_ADDRESS}")

            while True:
                # Read feed and water times
                time_data_water = await client.read_gatt_char(WATER_BIRDS_UUID)
                time_deg_c = _decode_time(time_data_water) 
                print(f"Time of watering: {time_deg_c}")
                time_data_feed = await client.read_gatt_char(FEED_BIRDS_UUID)
                time_deg_c = _decode_time(time_data_feed)
                print(f"Time of feeding: {time_deg_c}")
                #read humidity data
                humidity_data = await client.read_gatt_char(HUMIDITY_CHAR_UUID)
                humidity_deg_c = _decode_temperature(humidity_data)
                print(f"Humidity: {humidity_deg_c:.2f}%")
                # Read temperature
                temp_data = await client.read_gatt_char(TEMP_CHAR_UUID)
                temp_deg_c = _decode_temperature(temp_data)
                print(f"Temperature: {temp_deg_c:.2f}°C")

              
                
                await asyncio.sleep(2)

    except Exception as e:
        print(f"Error: {e}")

async def web_server():
    app = web.Application()
    app['pump_in'] = False
    app['pump_out'] = False
    
    # Add routes
    app.router.add_get('/', handle_root)
    app.router.add_get('/pump_in/{action}', handle_pump_in)
    app.router.add_get('/pump_out/{action}', handle_pump_out)
    app.router.add_get('/status', handle_status)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Web server started at http://0.0.0.0:8080")
    
    # Run forever
    while True:
        await asyncio.sleep(3600)  # Keep the server running

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Home Control webpage</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 40px; }
        .sensor-data { font-size: 24px; margin: 20px; }
        button { 
            padding: 15px 30px; 
            font-size: 18px; 
            margin: 10px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
        }
        .pump-in { background-color: #4CAF50; color: white; }
        .pump-out { background-color: #f44336; color: white; }
        .status { margin-top: 20px; }
    </style>
    <script>
        function controlPump(pump, action) {
            fetch(`/${pump}/${action}`)
                .then(response => {
                    updateButtonStates();
                });
        }

        function updateButtonStates() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('pump-in-state').textContent = data.pump_in ? 'ON' : 'OFF';
                    document.getElementById('pump-out-state').textContent = data.pump_out ? 'ON' : 'OFF';
                });
        }

        setInterval(updateButtonStates, 1000);
    </script>
</head>
<body>
    <h1>Home Control webpage</h1>
    
    <div class="sensor-data">
        <h2>Temperature: %.1f&#176;C</h2>
        <h2>Humidity: %.1f%%</h2>
    </div>

    <div class="controls">
        <button class="pump-in" onclick="controlPump('pump_in', 'on')">Pump In ON</button>
        <button class="pump-in" onclick="controlPump('pump_in', 'off')">Pump In OFF</button>
        <br>
        <button class="pump-out" onclick="controlPump('pump_out', 'on')">Pump Out ON</button>
        <button class="pump-out" onclick="controlPump('pump_out', 'off')">Pump Out OFF</button>
    </div>

    <div class="status">
        <p>Pump In Status: <span id="pump-in-state">%s</span></p>
        <p>Pump Out Status: <span id="pump-out-state">%s</span></p>
    </div>
</body>
</html>
"""

async def handle_root(request):
    # Simulated sensor data (replace with real readings)
    temperature = 25.0
    humidity = 50.0
    
    html = HTML_TEMPLATE % (
        temperature,
        humidity,
        "ON" if request.app['pump_in'] else "OFF",
        "ON" if request.app['pump_out'] else "OFF"
    )
    return web.Response(text=html, content_type='text/html')

async def handle_pump_in(request):
    action = request.match_info['action']
    request.app['pump_in'] = (action == 'on')
    return web.Response(text=f"Pump IN set to {action.upper()}")

async def handle_pump_out(request):
    action = request.match_info['action']
    request.app['pump_out'] = (action == 'on')
    return web.Response(text=f"Pump OUT set to {action.upper()}")

async def handle_status(request):
    return web.json_response({
        'pump_in': request.app['pump_in'],
        'pump_out': request.app['pump_out']
    })            

async def main():
    t1 = asyncio.create_task(BLE_task())
    t2 = asyncio.create_task(web_server())
    await asyncio.gather(t1, t2)

if __name__ == "__main__":
    asyncio.run(main())