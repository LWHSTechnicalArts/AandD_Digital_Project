import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import time
import json
import board
import terminalio
from adafruit_display_text import bitmap_label

red = 0xFF0000
purple = 0xFF00FF

# URLs to fetch from
APPID = "YOUR API KEY HERE" #get api key here: https://openweathermap.org/api
JSON_DATA_URL = f"http://api.openweathermap.org/data/2.5/weather?q=94112,us&APPID={APPID}&units=imperial"

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!"%secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

while True:
    response = requests.get(JSON_DATA_URL)
    #print(response.json())
    weather_data = response.json()
    temperature = weather_data["main"]["temp"] 
    location = weather_data["name"] 
    
    text = f"It's currently \n{temperature} degrees \nin {location}."  #\n creates a new line
    scale = 2

    text_area = bitmap_label.Label(terminalio.FONT, text=text, scale=scale, color=red)
    text_area.x = 10
    text_area.y = 20
    board.DISPLAY.show(text_area)

    time.sleep(30)




