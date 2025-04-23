#Make sure you have the adafruit_reqests, adafruit_connection_manager, and adafruit_display_text libraries.

import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import time

# URLs to fetch from
TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_QUOTES_URL = "https://www.adafruit.com/api/quotes.php"

# ==================== INTERNET CONNECTION ====================
def connect_to_wifi():
    for net in secrets['wifi']:
        try:
            print(f"Trying to connect to {net['ssid']}...")
            wifi.radio.connect(net['ssid'], net['password'])
            print("Connected to", net['ssid'])
            print("IP address:", wifi.radio.ipv4_address)
            return True
        except Exception as e:
            print(f"Failed to connect to {net['ssid']}: {e}")
            time.sleep(1)
    print("Could not connect to any known Wi-Fi network.")
    return False

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("ESP32-S2 WebClient Test")

print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

print("Available WiFi networks:")
for network in wifi.radio.start_scanning_networks():
    print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
            network.rssi, network.channel))
wifi.radio.stop_scanning_networks()

connect_to_wifi()

ipv4 = ipaddress.ip_address("8.8.4.4")
print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4)*1000))

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

while True:
    print("Fetching json from", JSON_QUOTES_URL)
    response = requests.get(JSON_QUOTES_URL)
    print("-" * 40)
    print(response.json())
    print("-" * 40)

    time.sleep(10)
