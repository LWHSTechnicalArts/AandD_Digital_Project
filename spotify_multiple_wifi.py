# Jeff Trevino, 12/4/24 with minor input from A.Kleindolph and Chatgpt :)
# Run this program to test out Spotify API access token fetch and refresh.

# ==================== IMPORTS ====================
import adafruit_binascii
from adafruit_datetime import datetime, timedelta
import adafruit_requests
import ipaddress
import json
import os
import socketpool
import ssl
import time
import wifi
import board
import displayio
from adafruit_display_text import bitmap_label
from adafruit_bitmap_font import bitmap_font
import terminalio

from my_spotify_creds import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
CURRENT_TRACK_URL = "https://api.spotify.com/v1/me/player/currently-playing"
CACHED_TOKEN_PATH = 'token.json'

ENCODED_CLIENT_ID_AND_SECRET_STRING = adafruit_binascii.b2a_base64((SPOTIFY_CLIENT_ID + ':' + SPOTIFY_CLIENT_SECRET).encode())[:-1] # in CircuitPython...

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

# ==================== AUTHORIZATION ====================
def get_first_access_token_interactive():
    # ask user to input authorization code extracted from authorization code endpoint redirect URI
    authorization_code = input("Enter authorization code from redirect URL:")

    # use authorization code to fetch an access token
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {ENCODED_CLIENT_ID_AND_SECRET_STRING.decode('ascii')}'
    }

    token_request_payload = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
    }

    access_token_response = requests.request(method='POST', url=TOKEN_URL, data=token_request_payload, headers=headers)
    return json.loads(access_token_response.content.decode('utf-8')) # return a dict

def get_fresh_access_token(path_to_token_json):
    # get refresh token from cached token JSON
    with open(path_to_token_json, 'r') as token_file:
        cached_token_json = json.load(token_file)
    refresh_token = cached_token_json['refresh_token']

    # use refresh token to get a fresh access token
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {ENCODED_CLIENT_ID_AND_SECRET_STRING.decode('ascii')}'
    }

    token_refresh_payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    print(f"requesting fresh access token using refresh token found in {CACHED_TOKEN_PATH}...")
    fresh_token_response = requests.request(method='POST', url=TOKEN_URL, data=token_refresh_payload, headers=headers)
    return json.loads(fresh_token_response.content.decode('utf-8')) # return a dict

def cache_access_token(access_token_json, cache_path):
    """
    Write the access token JSON to the file system.
    """
    print(f"access token contains a refresh token! — caching access token at {cache_path}...")
    with open(cache_path, 'w+') as access_token_cache_file:
        json.dump(access_token_json, access_token_cache_file)

def cached_token_exists(CACHED_TOKEN_PATH):
    try:
        os.stat(CACHED_TOKEN_PATH)
        return True
    except:
        return False

def ensure_access_token(access_token):
    access_token_json_contains_refresh_token = lambda json_dict: True if 'refresh_token' in json_dict else False
    if cached_token_exists(CACHED_TOKEN_PATH):
        access_token = get_fresh_access_token(access_token)
    else:
        access_token = get_first_access_token_interactive()

    if 'refresh_token' in access_token:
            cache_access_token(access_token, CACHED_TOKEN_PATH)
    return access_token

# ==================== CURRENTLY PLAYING TRACK ====================
def get_currently_playing_track(access_token):
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Bearer {}'.format(access_token)
    }

    print('requesting currently playing track data...')
    try:
        currently_playing_response = requests.request('GET', CURRENT_TRACK_URL, headers=headers)
        # Handle non-200 status codes
        if currently_playing_response.status_code == 204:
            print("No content - nothing is playing right now.")
            return None
        elif currently_playing_response.status_code == 401:
            print("Unauthorized - access token may be expired.")
            return None
        elif currently_playing_response.status_code != 200:
            print(f"Error: Received unexpected status code {currently_playing_response.status_code}")
            return None

        try:
            data = json.loads(currently_playing_response.content.decode('utf-8'))
            if not data:  # Check if the response is empty
                print("No track data available.")
                return None
            return data
        except json.JSONDecodeError:
            print("Error decoding JSON response.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# ==================== DATA WRANGLING ====================
def print_currently_playing(cp_json):
    """
    Extracts and displays the current song and artist(s) on the display.
    """
    try:
        if cp_json is None or "item" not in cp_json or cp_json["item"] is None:
            artist_text = ""
            song_text = "No song playing"
            artist_names = "Unknown Artist"
            song_name = "No song playing"
        else:
            # Extract song name
            song_name = cp_json["item"]["name"]

            # Extract artist(s) and format them as "Artist1, Artist2"
            artists = cp_json["item"]["artists"]
            artist_names = ", ".join(artist["name"] for artist in artists)

            # Wrap text
            artist_text = wrap_text(artist_names, max_line_length=19)
            song_text = wrap_text(song_name, max_line_length=19)

        # Display the text on the screen with different colors
        group = displayio.Group()

        artist_label = bitmap_label.Label(terminalio.FONT, text=artist_text, scale=2, color=0xFFFF00)
        artist_label.x = 5
        artist_label.y = 10
        group.append(artist_label)

        # Adjust song label position based on artist text height
        song_label_y = artist_label.y + (artist_label.bounding_box[3] * artist_label.scale + 10)
        song_label = bitmap_label.Label(terminalio.FONT, text=song_text, scale=2, color=0x00FF00)
        song_label.x = 5
        song_label.y = song_label_y
        group.append(song_label)

        board.DISPLAY.root_group = group

        print(f"Now Playing: {artist_names} - {song_name}")  # Debugging output in console

    except KeyError as e:
        print(f"Error extracting currently playing track data: {e}")
        error_label = bitmap_label.Label(terminalio.FONT, text="Error fetching track", scale=2, color=0xFF0000)
        error_label.x = 10
        error_label.y = 50
        board.DISPLAY.root_group = displayio.Group()
        board.DISPLAY.root_group.append(error_label)

# ==================== TEXT WRAPPING FUNCTION ====================

def wrap_text(text, max_line_length):
    words = text.split()
    wrapped_lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= max_line_length:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            wrapped_lines.append(current_line)
            current_line = word

    if current_line:
        wrapped_lines.append(current_line)

    return "\n".join(wrapped_lines)

# ==================== MAIN ====================
expiration_time = datetime.now() # assume token expiration to force fresh token on start
access_token_json = None
access_token_is_expired = lambda expiration_time: True if datetime.now() >= expiration_time else False
while True:
    if access_token_is_expired(expiration_time):
        print(f"\n\nretrieving refresh token from {CACHED_TOKEN_PATH}...")
        access_token_json = ensure_access_token(CACHED_TOKEN_PATH)
        print(f"\n\nfetched fresh token: {access_token_json['access_token']}")
        expiration_time = datetime.now() + timedelta(seconds=3599)

    response = get_currently_playing_track(access_token_json['access_token'])
    # case when Spotify is not open in a tab or has stopped playing for a long time
    if not response:
        print('connected - awaiting playback...')
        cp_json = None
        print_currently_playing(cp_json)
        time.sleep(2)
        continue

    # case when commercial is playing
    elif not response['item']:
        print('commercial...')
        time.sleep(2)
        continue

    else:
        currently_playing = response
        #print(json.dumps(currently_playing))
        print_currently_playing(currently_playing)

    time.sleep(10)
