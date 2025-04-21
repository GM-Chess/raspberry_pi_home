# import time
# from machine import Pin, I2C
# import network
# import socket

# # Sensor settings
# SENSOR_ADDR = 0x38
# CMD_GET_STATUS = 0x71
# CMD_TRIGGER_MEAS = 0xAC

# # CRC-8 function
# def crc8(data):
#     crc = 0xFF
#     for byte in data:
#         crc ^= byte
#         for _ in range(8):
#             if crc & 0x80:
#                 crc = (crc << 1) ^ 0x31
#             else:
#                 crc <<= 1
#             crc &= 0xFF
#     return crc

# # Initialize I2C
# i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100_000)

# # Pump control pins
# pump_in = Pin(14, Pin.OUT)
# pump_out = Pin(15, Pin.OUT)
# pump_in.off()
# pump_out.off()

# # LED
# led = Pin('LED', Pin.OUT)

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



# while True:
#     try:
#         cl, addr = s.accept()
#         request = cl.recv(1024)
#         request = str(request)
        
#         # Get sensor data
#         temperature, humidity = read_temperature_humidity()
        
#         # Handle pump control requests
#         if '/pump_in/on' in request:
#             pump_in.on()
#         elif '/pump_in/off' in request:
#             pump_in.off()
#         elif '/pump_out/on' in request:
#             pump_out.on()
#         elif '/pump_out/off' in request:
#             pump_out.off()
#         elif '/status' in request:
#             status = {
#                 'pump_in': pump_in.value(),
#                 'pump_out': pump_out.value()
#             }
#             response = str(status).replace("'", '"')
#             cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
#             cl.send(response)
#             cl.close()
#             continue

#         # Generate HTML response
#         response = html_template % (
#             temperature if isinstance(temperature, float) else 0.0,
#             humidity if isinstance(humidity, float) else 0.0,
#             "ON" if pump_in.value() else "OFF",
#             "ON" if pump_out.value() else "OFF"
#         )

#         cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
#         cl.send(response)
#         cl.close()
        
#         # Toggle LED for visual feedback
#         led.toggle()

#     except Exception as e:
#         print("Connection error:", e)
#         cl.close()
# Pico Script (MicroPython)
import aioble
import uasyncio as asyncio
import json
from machine import Pin, I2C, PWM
import time
import random
import struct
from bluetooth import UUID

# Custom UUIDs for our service and characteristics
_ENVIRONMENTAL_SERVICE_UUID = UUID("932c32bd-0000-47a2-835a-a8d455b859dd")
_TEMP_CHAR_UUID = UUID("932c32bd-0001-47a2-835a-a8d455b859dd")
_HUMIDITY_CHAR_UUID = UUID("932c32bd-0002-47a2-835a-a8d455b859dd")
_PUMP_CONTROL_UUID = UUID("932c32bd-0003-47a2-835a-a8d455b859dd")
_LED_CONTROL_UUID = UUID("932c32bd-0004-47a2-835a-a8d455b859dd")
_WATER_BIRDS_UUID = UUID("932c32bd-0005-47a2-835a-a8d455b859dd")
_FEED_BIRDS_UUID = UUID("932c32bd-0006-47a2-835a-a8d455b859dd")
_MANUAL_FEED_BIRDS_UUID = UUID("932c32bd-0007-47a2-835a-a8d455b859dd")

# Initialize hardware
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100_000)

# Sensor settings
SENSOR_ADDR = 0x38
CMD_GET_STATUS = 0x71
CMD_TRIGGER_MEAS = 0xAC

# Pump control pins
pump_in = Pin(14, Pin.OUT)
pump_out = Pin(15, Pin.OUT)
led = Pin('LED', Pin.OUT)
servo_out = PWM(Pin(14))
servo_in = PWM(Pin(17)) #make sure this can be used for servo on pico 

# Turn everything off initially
pump_in.off()
pump_out.off()
led.off()

#PWM parameters
FREQUANCY = 50
MAX_ANGLE = 180
MIN_ANGLE = 0
servo_in.freq(FREQUANCY)
servo_out.freq(FREQUANCY)
servo_in.duty_u16(0)
servo_out.duty_u16(0)


# Create BLE service and characteristics
environmental_service = aioble.Service(_ENVIRONMENTAL_SERVICE_UUID)

# Temperature Characteristic (read/notify)
temp_char = aioble.Characteristic(
    environmental_service,
    _TEMP_CHAR_UUID,
    read=True,
    notify=True,
    capture=True,
)

# Humidity Characteristic (read/notify)
humidity_char = aioble.Characteristic(
    environmental_service,
    _HUMIDITY_CHAR_UUID,
    read=True,
    notify=True,
)

# Pump Control Characteristic (write)
pump_control_char = aioble.Characteristic(
    environmental_service,
    _PUMP_CONTROL_UUID,
    write=True,
    write_no_response=True,
    capture=True,
)

# LED Control Characteristic (write)
led_control_char = aioble.Characteristic(
    environmental_service,
    _LED_CONTROL_UUID,
    write=True,
    write_no_response=True,
    capture=True,
)

# LED Birds Characteristic (read)
water_birds_char = aioble.Characteristic(
    environmental_service,
    _WATER_BIRDS_UUID,
    read=True,
    notify=True,
)
# Feed Birds Characteristic (read)
feed_birds_char = aioble.Characteristic(
    environmental_service,
    _FEED_BIRDS_UUID,
    read=True,
    notify=True,    
)
# Manual Feed Birds Characteristic (write)
manual_feed_birds_char = aioble.Characteristic(
    environmental_service,
    _MANUAL_FEED_BIRDS_UUID,
    write=True,
    write_no_response=True,
    capture=True,
)
# Register services
aioble.register_services(environmental_service)

# CRC-8 function
def crc8(data):
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc <<= 1
            crc &= 0xFF
    return crc

def read_temperature_humidity():
    try:
        # Existing sensor reading code
        status = i2c.readfrom_mem(SENSOR_ADDR, CMD_GET_STATUS, 1)[0]
        if (status & 0x18) != 0x18:
            i2c.writeto_mem(SENSOR_ADDR, 0x1B, b'\x00')
            i2c.writeto_mem(SENSOR_ADDR, 0x1C, b'\x00')
            i2c.writeto_mem(SENSOR_ADDR, 0x1E, b'\x00')
            time.sleep_ms(10)

        i2c.writeto(SENSOR_ADDR, bytes([CMD_TRIGGER_MEAS, 0x33, 0x00]))
        time.sleep_ms(10)

        start_time = time.ticks_ms()
        while True:
            status = i2c.readfrom_mem(SENSOR_ADDR, CMD_GET_STATUS, 1)[0]
            if not (status & 0x80):
                break
            if time.ticks_diff(time.ticks_ms(), start_time) > 1000:
                raise TimeoutError("Measurement timeout")
            time.sleep_ms(10)

        data = i2c.readfrom(SENSOR_ADDR, 7)
        received_crc = data[-1]
        calculated_crc = crc8(data[0:6])

        if calculated_crc != received_crc:
            return "CRC Error", ""

        humidity_raw = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
        temperature_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

        humidity = (humidity_raw / (2**20)) * 100
        temperature = (temperature_raw / (2**20)) * 200 - 50
        
        return temperature, humidity
    
    except Exception as e:
        print("Sensor error:", e)
        return "Error", ""

def interval_mapping(x, in_min, in_max, out_min, out_max):
    """
    Maps a value from one range to another.
    This function is useful for converting servo angle to pulse width.
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def servo_position(servo, angle):
    """Set servo position"""
    try:
   
        pulse_width = interval_mapping(
            angle, 0, 180, 0.5, 2.5
        )  # Map angle to pulse width in ms
        duty = int(
            interval_mapping(pulse_width, 0, 20, 0, 65535)
        )  # Map pulse width to duty cycle
        servo.duty_u16(duty)  # Set PWM duty cycle

    except Exception as e:
        print("Servo error:", e)

def process_pump_control(data):
    """Handle pump control commands"""
    try:
        if data ==  b"\x01":
            pump_in.on()
        elif data == b"\x00":
            pump_in.off()
        elif data == b"\x10":
            pump_out.off()
        elif data == b"\x11":
            pump_out.on()
        else:
            pump_in.off()
            pump_out.off()
        return int(time.time() * 10000000)
        
    except Exception as e:
        print("Error processing pump control:", e)

def process_led_control(data):
    """Handle LED control commands"""
    try:
        led.value(int.from_bytes(data, 'little'))
    except Exception as e:
        print("Error processing LED control:", e)

async def water_birds():
    """waters the birds on schedule"""
    try:
        pump_out.on()
        await asyncio.sleep(5) #turn on pump for 5 seconds to drain the water
        pump_out.off()
        pump_in.on()
        await asyncio.sleep(3) #turn on pump for 5 seconds to fill the water
        pump_in.off()
        # Add logic to control water birds here
        return int(time.time()  * 10000000)
    except Exception as e:
        print("Water birds error:", e)

async def feed_birds():
    """feeds the birds on schedule"""
    try:
        servo_position(servo_out, 90) #open the bottom of the feeder to remove the old food
        await asyncio.sleep(5) #turn on pump for 5 seconds to drain the water
        servo_position(servo_out, 0) #close the bottom of the feeder to remove the old food
        servo_position(servo_in, 90) #open the top of the feeder to fill the food
        await asyncio.sleep(5) #turn on pump for 5 seconds to fill the water
        servo_position(servo_in, 0) #close the top of the feeder to fill the food
        return int(time.time() * 10000000)
    except Exception as e:
        print("Feed birds error:", e)
        return 0  # Example implementation
    
async def birds_task():
    """Water and feed the birds on schedule."""
    while True:
        try:
            # Await the async functions to get actual values
            last_water_bird = await water_birds()
            last_feed_bird = await feed_birds()

            # Pack as 8-byte signed integers
            water_birds_char.write(struct.pack("<q", last_water_bird))
            feed_birds_char.write(struct.pack("<q", last_feed_bird))
            
            # Notify with 8-byte data
            feed_birds_char.notify(struct.pack("<q", last_feed_bird))
            water_birds_char.notify(struct.pack("<q", last_water_bird))
        
        except Exception as e:
            print("Water birds error:", e)
        await asyncio.sleep(1)  # Adjust sleep time after testing

async def sensor_task():
    """Main sensor reading and update task"""
    while True:
        try:
            # Read sensor values (replace with actual sensor reading)
            tempature, humidity = read_temperature_humidity()
      
            # Update characteristics
            temp_char.write(struct.pack("<h", int(tempature * 100)))
            humidity_char.write(struct.pack("<h", int(humidity * 100)))
            
            # Send notifications
            temp_char.notify(struct.pack("<h", int(tempature * 100)))
            humidity_char.notify(struct.pack("<h", int(humidity * 100)))
            
            
        except Exception as e:
            print("Sensor error:", e)
        
        await asyncio.sleep(300)

async def ble_control_task():
    """Handle incoming BLE commands"""
    while True:
        try:
            data = pump_control_char.read()
            if data:
                update_time = process_pump_control(data)
                water_birds_char.write(struct.pack("<q", update_time))
                water_birds_char.notify(struct.pack("<q", update_time))
        except Exception as e:
            print("Error processing pump control:", e)
        
        try:
            data = led_control_char.read()
            if data:
                process_led_control(data)
        except Exception as e:
            print("Error processing LED control:", e)

        try:  
            data = manual_feed_birds_char.read()
            if data == b"\x01":
                manual_bird_fed = feed_birds()
                feed_birds_char.write(struct.pack("<q", manual_bird_fed))
                feed_birds_char.notify(struct.pack("<q", manual_bird_fed))  
        except Exception as e:
            print("Error processing manual feed birds:", e)        
            
        await asyncio.sleep_ms(100)

async def peripheral_task():
    """BLE advertising and connection management"""
    while True:
        async with await aioble.advertise(
            250_000,  # Advertising interval
            name="WEED_420",
            services=[_ENVIRONMENTAL_SERVICE_UUID],
            appearance=0x0340  # Generic sensor appearance
        ) as connection:
            print("Client connected:", connection.device)
            await connection.disconnected()
            print("Client disconnected")

async def main():
    """Main application entry point"""
    t1 = asyncio.create_task(sensor_task())
    t2 = asyncio.create_task(ble_control_task())
    t3 = asyncio.create_task(peripheral_task())
    t4 = asyncio.create_task(birds_task())
    await asyncio.gather(t1, t2, t3,t4)

asyncio.run(main())
# async def main():
#     # Register the service and characteristic
#     service = aioble.Service(_SERVICE_UUID)
#     char = aioble.Characteristic(
#         service, 
#         _CHAR_UUID, 
#         read=True,  # Allow reads
#         notify=True,  # Allow notifications
#         initial="Hi from Pico"  # Initial value
#     )
#     aioble.register_services(service)

#     Connection = await aioble.advertise(
#             _ADV_INTERVAL_US,
#             name="temp-sense",
#             services=[_SERVICE_UUID],
#             appearance=_PICO_NAME,
#             manufacturer=(0xabcd, b"1234"),
#         )
#     print("Connection from", device)

#     # Advertise
#     await aioble.advertise(
#         name="Pico-BLE",
#         services=[_SERVICE_UUID],
#         interval_us=100_000,
#     )
#     print("Advertising...")

#     # Wait for a connection
#     while not aioble.Connection.connected():
#         await asyncio.sleep(1)
#     print("Connected!")
    
#     #read from client
#     while True:
#         data = await char.read()
#         print("Received data:", data)
#         # Echo the data back to the client
#         await char.write(data)
#         print("Sent data back to client:", data)    
#         await asyncio.sleep(1)
        
# if __name__ == "__main__":
#     while True:
#         asyncio.run(main())