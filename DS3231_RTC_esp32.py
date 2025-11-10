#works with circuitPython 9
#print time and date on ESP32-S3 LCD screen
import busio
import terminalio
from adafruit_display_text import bitmap_label
import time
import board
import adafruit_ds3231

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
rtc = adafruit_ds3231.DS3231(i2c)

yellowy = 0x99FF22
days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")

if False:   # change to True if you want to write the time!
    #                     year, mon, date, hour, min, sec, wday, yday, isdst
    t = time.struct_time((2025,  11,   10,   10,  35,  00,    1,   -1,    -1))
    # you must set year, mon, date, hour, min, sec and weekday
    # yearday is not supported, isdst can be set but we don't do anything with it at this time
    print("Setting time to:", t)     # uncomment for debugging
    rtc.datetime = t
    print()

while True:
    t = rtc.datetime
    #print(t)     # uncomment for debugging
    print("The date is %s %d/%d/%d" % (days[t.tm_wday], t.tm_mon, t.tm_mday, t.tm_year))
    print("The time is %d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec))
    time.sleep(1) # wait a second
    text = " %s" % (days[t.tm_wday]) + "\n %d/%d/%d" % (t.tm_mon, t.tm_mday, t.tm_year) +"\n %d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec)
    # Update this to change the size of the text displayed. Must be a whole number.
    scale = 3
    text_area = bitmap_label.Label(terminalio.FONT, text=text, scale=scale, color=yellowy)
    text_area.x = 5
    text_area.y = 20
    board.DISPLAY.root_group = (text_area)
    time.sleep (0.1)
