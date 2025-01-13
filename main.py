import network
import socket
import machine
import ujson
from time import sleep

ssid = "iPhone"
password = "aemn9yfrs5e3t"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

print('Waiting for connection...')
while wlan.status() != network.STAT_GOT_IP:
    sleep(1)

status = wlan.ifconfig()
ip_address = status[0]
print(f'Connected to {ssid}')
print(f'Pico W IP Address: {ip_address}')

# GPIO setup for fan and heater
fan = machine.Pin(16, machine.Pin.OUT)
heater = machine.Pin(17, machine.Pin.OUT)

# Setup internal temperature sensor
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / 65535

# Socket setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ip_address, 5002))
s.listen(1)
print('Waiting for a connection...')

# Handle client connections
try:
    while True:
        conn, addr = s.accept()
        print('Connection from', addr)

        data = conn.recv(1024).decode()
        if not data:
            print('No data received.')
            conn.close()
            continue

        print('Received:', data)
        command = ujson.loads(data)

        # Check if the command contains "read": "send_temp"
        if 'read' in command and command['read'] == 'send_temp':
            reading = sensor_temp.read_u16() * conversion_factor
            temperature = 27 - (reading - 0.706) / 0.001721
            response = ujson.dumps({'temperature': f'{temperature:.2f}'})
            conn.send(response.encode())
            print(f'Sent temperature: {temperature:.2f}°C')

        # Control the fan
        if 'gpio' in command:
            if command['gpio'] == 'on':
                fan.value(1)
                print('Fan turned ON')
            elif command['gpio'] == 'off':
                fan.value(0)
                print('Fan turned OFF')

        # Control the heater
        if 'gpio1' in command:
            if command['gpio1'] == 'on':
                heater.value(1)
                print('Heater turned ON')
            elif command['gpio1'] == 'off':
                heater.value(0)
                print('Heater turned OFF')

        conn.close()

except KeyboardInterrupt:
    print('Server shutting down...')

finally:
    s.close()
    print('Socket closed.')