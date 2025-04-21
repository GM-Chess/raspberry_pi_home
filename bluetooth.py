# Pi Zero Script (Python 3)
import asyncio
import struct
from bleak import BleakClient
import time
import socket
import http.server
import socketserver
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
PUMP_CONTROL_UUID = "932c32bd-0003-47a2-835a-a8d455b859dd"
LED_CONTROL_UUID = "932c32bd-0004-47a2-835a-a8d455b859dd"  # Custom LED UUID (MUST MATCH PICO)
WATER_BIRDS_UUID = "932c32bd-0005-47a2-835a-a8d455b859dd"
FEED_BIRDS_UUID = "932c32bd-0006-47a2-835a-a8d455b859dd"
MANUAL_FEED_BIRDS_UUID = "932c32bd-0007-47a2-835a-a8d455b859dd"

def get_ip():
    """Get actual IP address of the Raspberry Pi"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

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

class SensorData:
    def __init__(self):
        self.temperature = 14.5
        self.humidity = 12.4
        self._lock = asyncio.Lock()
        
    async def update(self, temp, humidity, fed_time, water_time):
        async with self._lock:
            self.temperature = temp
            self.humidity = humidity
            self.fed_time = fed_time
            self.water_time = water_time
            
    async def get_values(self):
        async with self._lock:
            return (self.temperature, self.humidity, self.fed_time, self.water_time)

sensor_data = SensorData()

class BLEController:
    def __init__(self):
        self.client = None
        self.connected = False
        
    async def connect(self):
        self.client = BleakClient(PICO_ADDRESS)
        await self.client.connect()
        self.connected = True
        print("Connected to BLE device")
        
    async def disconnect(self):
        if self.connected:
            await self.client.disconnect()
            self.connected = False
            
    async def control_led(self, state: bool):
        if not self.connected:
            raise ConnectionError("Not connected to BLE device")
            
        value = b"\x01" if state else b"\x00"
        await self.client.write_gatt_char(LED_CONTROL_UUID, value)
        print(f"LED set to {'ON' if state else 'OFF'}")

# Shared BLE controller instance
ble_controller = BLEController()

# Update HTML template to add LED control
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Home Control webpage</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            margin: 40px; 
        }
        .sensor-data { 
            font-size: 24px; 
            margin: 20px; 
        }
        .timestamps {
            font-size: 18px; 
            margin: 20px; 
        }
        button { 
            padding: 15px 30px; 
            font-size: 18px; 
            margin: 10px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
        }
        .pump-in { 
            background-color: #4CAF50; 
            color: white; 
        }
        .pump-out { 
            background-color: #f44336; 
            color: white; 
        }
        .led-on {
            background-color: #2196F3;
            color: white;
        }
        .led-off {
            background-color: #607D8B;
            color: white;
        }
        .status { 
            margin-top: 20px; 
        }
        .led-control {
            margin-top: 30px;
            padding: 20px;
            border-top: 1px solid #ddd;
        }
        
        .feed-button {
            background-color: #FF9800;
            color: white;
        }
    </style>
    <script>
        function feedBirds() {
            fetch('/feed')
                .then(response => {
                    if (!response.ok) throw new Error('Feeding failed');
                    updateTimestamps();
                })
                .catch(error => console.error('Error:', error));
        }

        function controlPump(pump, action) {
            fetch(`/${pump}/${action}`)
                .then(updateButtonStates);
        }

        function controlLED(state) {
            fetch(`/led/${state}`)
                .then(updateButtonStates);
        }

         function updateButtonStates() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('pump-in-state').textContent = data.pump_in ? 'ON' : 'OFF';
                    document.getElementById('pump-out-state').textContent = data.pump_out ? 'ON' : 'OFF';
                    document.getElementById('led-state').textContent = data.led_state ? 'ON' : 'OFF';
                    document.getElementById('last-fed').textContent = data.last_fed;
                    document.getElementById('last-watered').textContent = data.last_watered;
                });
        }

        // Initial update and set interval
        document.addEventListener('DOMContentLoaded', updateButtonStates);
        setInterval(updateButtonStates, 1000);
    </script>
</head>
<body>
    <h1>Home Control webpage</h1>
    
    <div class="sensor-data">
        <h2>Temperature: %.1f&#176;C</h2>
        <h2>Humidity: %.1f%%</h2>
    </div>
    <div class="timestamps">
        <h2>Last Fed: %s</h2>
        <h2>Last Watered: %s</h2>
    </div>
    <div class="controls">
        <button class="feed-button" onclick="feedBirds()">FEED BIRDS NOW</button>
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

    <div class="led-control">
        <h2>LED Control</h2>
        <button class="led-on" onclick="controlLED('on')">LED ON</button>
        <button class="led-off" onclick="controlLED('off')">LED OFF</button>
        <p>LED Status: <span id="led-state">%s</span></p>
    </div>
</body>
</html>"""


async def web_server(ble_client):
    """Start the web server and handle requests."""
    app = web.Application(middlewares=[error_middleware])
    app = web.Application()
    
    app['ble_client'] = ble_client  # Store BLE client in app context
    app['pump_in'] = False
    app['pump_out'] = False
    app['led_state'] = False
    app['last_fed'] = "Never"
    app['last_watered'] = "Never"
    
    # Add new route for LED control
    app.router.add_get('/', handle_root)
    app.router.add_get('/pump_in/{action}', handle_pump_in)
    app.router.add_get('/pump_out/{action}', handle_pump_out)
    app.router.add_get('/led/{state}', handle_led)  
    app.router.add_get('/status', handle_status)   
    app.router.add_get('/feed', handle_feed)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print(f"Server running on http://{get_ip()}:8080")  # Now using the defined function
    
    # Run forever
    while True:
        await asyncio.sleep(3600)

@web.middleware
async def error_middleware(request, handler):
    """Middleware to handle errors and return JSON responses."""
    try:
        return await handler(request)
    except web.HTTPException as ex:
        return web.json_response({
            "error": ex.reason,
            "status": ex.status
        }, status=ex.status)
    except Exception as e:
        return web.json_response({
            "error": str(e),
            "status": 500
        }, status=500)

async def handle_status(request):
    """ set up JSON for the status """
    return web.json_response({
        'pump_in': request.app['pump_in'],
        'pump_out': request.app['pump_out'],
        'led_state': request.app['led_state'],  
        'last_fed': request.app['last_fed'],
        'last_watered': request.app['last_watered']
    })
async def handle_led(request):
    """Handle LED control of the app to the Pico via BLE"""
    try:
        action = request.match_info['state']
        request.app['led_state'] = (action == 'on')
        
        # Get BLE client from app context
        ble_client = request.app['ble_client']
        
        if ble_client and ble_client.is_connected:
            led_value = b"\x01" if (action == 'on') else b"\x00"
            await ble_client.write_gatt_char(LED_CONTROL_UUID, led_value)
            return web.Response(text=f"LED set to {action.upper()}")
        else:
            return web.Response(text="BLE not connected", status=503)
            
    except KeyError:
        return web.Response(text="Missing state parameter", status=400)
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_feed(request):
    try:
        ble_client = request.app['ble_client']
        if ble_client and ble_client.is_connected:
            # Write feed command
            await ble_client.write_gatt_char(MANUAL_FEED_BIRDS_UUID, b"\x01")
            # Update timestamp
            request.app['last_fed'] = _decode_time(await ble_client.read_gatt_char(FEED_BIRDS_UUID))
            return web.Response(text="Birds fed successfully")
        return web.Response(text="BLE not connected", status=503)
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_pump_in(request):
    """Handle pump in control"""
    try:
        action = request.match_info['action']
        request.app['pump_in'] = (action == 'on')
        ble_client = request.app['ble_client']
        if ble_client and ble_client.is_connected:
            pump_value = b"\x01" if (action == 'on') else b"\x00"
            await ble_client.write_gatt_char(PUMP_CONTROL_UUID, pump_value)
            request.app['last_watered'] = _decode_time(await ble_client.read_gatt_char(WATER_BIRDS_UUID))
        return web.Response(text=f"Pump IN set to {action.upper()}")
    except KeyError:
        return web.Response(text="Missing action parameter", status=400)
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_pump_out(request):
    """Handle pump out control"""
    try:
        action = request.match_info['action']
        request.app['pump_out'] = (action == 'on')
        ble_client = request.app['ble_client']
        if ble_client and ble_client.is_connected:
            pump_value = b"\x11" if (action == 'on') else b"\x10"
            await ble_client.write_gatt_char(PUMP_CONTROL_UUID, pump_value)
        return web.Response(text=f"Pump OUT set to {action.upper()}")
    except KeyError:
        return web.Response(text="Missing action parameter", status=400)
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_root(request):
    
    temp, humidity, fed_time, water_time = await sensor_data.get_values()
    
    html = HTML_TEMPLATE % (
        temp,
        humidity,
        fed_time,
        water_time,
        "ON" if request.app['pump_in'] else "OFF",
        "ON" if request.app['pump_out'] else "OFF",
        "ON" if request.app['led_state'] else "OFF"
    )
    return web.Response(text=html, content_type='text/html')

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

# Update BLE_task to maintain connection
async def BLE_task(ble_client):
    while True:
        try:
        
            print(f"Connected to Pico at {PICO_ADDRESS}")
            while True:
                # Read actual sensor data
                temp_data = await ble_client.read_gatt_char(TEMP_CHAR_UUID)
                humidity_data = await ble_client.read_gatt_char(HUMIDITY_CHAR_UUID)
                bird_fed_time = await ble_client.read_gatt_char(FEED_BIRDS_UUID)
                bird_water_time = await ble_client.read_gatt_char(WATER_BIRDS_UUID)
                # Decode values
                temp = _decode_temperature(temp_data)
                humidity = _decode_temperature(humidity_data)
                #print(f"Temperature: {temp:.2f}°C, Humidity: {humidity:.2f}%")
                
                # Update shared sensor data
                await sensor_data.update(temp, humidity, _decode_time(bird_fed_time), _decode_time(bird_water_time))
                
                await asyncio.sleep(2)
                    
        except Exception as e:
            print(f"BLE error: {e}")
            await asyncio.sleep(5)

# Update main to properly handle shutdown
async def main():
     # Initialize BLE client first
    ble_client = BleakClient(PICO_ADDRESS)
    await ble_client.connect()
    
    # Pass BLE client to web server
    t1 = asyncio.create_task(BLE_task(ble_client))
    t2 = asyncio.create_task(web_server(ble_client))
    
    await asyncio.gather(t1, t2)
    
    # Cleanup
    await ble_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())