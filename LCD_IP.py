import time
from RPLCD.i2c import CharLCD
import netifaces


lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2)


def get_local_ip():
    try:
        addresses = netifaces.ifaddresses("wlan0")
        ipv4_info = addresses[netifaces.AF_INET][0]
        return ipv4_info['addr']
    except (ValueError, KeyError):
        return "no wlan0 found"


str = get_local_ip()
print(f"{str}")
lcd.clear()
lcd.write_string(str)
