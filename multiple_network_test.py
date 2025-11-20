import wifi
import time

from secrets import secrets

# Connect to WiFi
for net in secrets['wifi']:
    try:
        wifi.radio.connect(net['ssid'], net['password'])
        print("Connected to", net['ssid'])
        break
    except Exception as e:
        time.sleep(1)

while True: 
    #your code here
    time.sleep(1)
