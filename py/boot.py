import network
import time
from machine import reset, Pin, RTC
from utils import (
    connect_to_wifi,
    set_rtc_from_internet,
    get_iso_datestr_from_rtc,
    blink_led,
    start_over
)
from config import (
    WIFIS_TO_TRY,
    WIFI_PW,
    WIFI_CONN_TIMEOUT_MS,
    COUCH_USER,
    COUCH_PW
)

from mysht30 import MySht30
import auth_urequests as urequests

EMBEDDED_LED = Pin(2, Pin.OUT)
PENDING_LED = Pin(18, Pin.OUT)
SUCCESS_LED = Pin(19, Pin.OUT)
ERROR_LED = Pin(21, Pin.OUT)

"""
Start by creating network station obj and trying to connect.
Stay in loop until we've connected
"""
try:
    print(f"Starting boot script...")

    # turn on yellow led as we process
    PENDING_LED.value(1)
    time.sleep(2)

    # start by creating network station obj
    clock = RTC()
    wifi_station = network.WLAN(network.STA_IF)
    if wifi_station.active():
        wifi_station.active(False)
        time.sleep(3)
    wifi_station.active(True)

    # if not connected, attempt to connect
    ms_to_connect = 0
    active_wifi = ''
    if not wifi_station.isconnected():
        for wifi in WIFIS_TO_TRY:  # wifi network options to attempt conn
            print(f"Trying to connect to WIFI {wifi}...")
            success, ms_to_connect = connect_to_wifi(wifi, WIFI_PW, wifi_station, timeout_ms=WIFI_CONN_TIMEOUT_MS)
            if success:  # break out if we connect successfully
                active_wifi = wifi
                print(f"Connected to WIFI {wifi} after {ms_to_connect}ms!")
                break
            else:
                print(f"Unable to connect to WIFI {wifi} after {ms_to_connect}ms")

        # if we can't connect, sleep then reset to retry
        if not wifi_station.isconnected():
            raise Exception('Unable to connect to wifi')
            # start_over(120)

        else:
            print(f"Connected to WIFI {active_wifi} after {ms_to_connect}ms!")

        # start processes that require internet
        # while wifi_station.isconnected():
    if clock.datetime()[0] < 2022:  # indicates RTC has not yet been set
        print(f"Trying to set RTC clock with world time API call")
        set_rtc_from_internet(clock)
    else:
        print(f"RTC clock already set, current time = {clock.datetime()}")

    sensor = MySht30()
    sensor.measure_int()  # take measurement, sets _current_data
    print(f"Sensor measurement recorded: temp: {sensor.current_temp_f}, hum: {sensor.current_humidity}")

    data = {
        'tempF': sensor.current_temp_f,
        'humRel': sensor.current_humidity,
        'dt': get_iso_datestr_from_rtc(clock),
        'loc': 'sauna',
        'timeToWifiConnMs': ms_to_connect,
        'wifi': active_wifi
    }

    doc_post = urequests.post('http://192.168.1.101:5984/home-sensors', json=data, auth=[COUCH_USER, COUCH_PW])
    PENDING_LED.value(0)
    if doc_post.status_code in [201, 200]:
        print(f"Success! doc posted to CouchDB")
        SUCCESS_LED.value(1)
    else:
        print(f"Unable to post doc, response code: {doc_post.status_code}")
        ERROR_LED.value(1)

    # sleep for a bit just to display either success or error led
    time.sleep(5)

except Exception as e:
    time.sleep(2)
    print(f"Error during script: {e}")
    time.sleep(2)
    PENDING_LED.value(0)
    ERROR_LED.value(1)
    time.sleep(10)
finally:
    EMBEDDED_LED.off()
    PENDING_LED.value(0)
    SUCCESS_LED.value(0)
    ERROR_LED.value(0)

    # keeps the script on and start reboot
    start_over(120)


