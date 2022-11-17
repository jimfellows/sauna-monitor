# import esp
from mysht30 import MySht30
from machine import (
    Pin,
    unique_id,
    deepsleep,
    lightsleep,
    RTC,
    reset
)
from config import (
    SLEEP_TIME_MS,
    WIFIS_TO_TRY,
    COUCH_DB_NAME,
    COUCH_USER,
    COUCH_PW,
    COUCH_IP,
    COUCH_PORT,
    WIFI_NAME,
    WIFI_PW,
    WIFI_CONN_TIMEOUT_MS,
    COUCH_BASE_URL
)
import time
import network
import auth_urequests as urequests
import os


def connect_to_wifi(wifi_name, wifi_pw, st_interface, timeout_ms=60000):
    """
    function to attempt connect to wifi/network object
    for use in loop to make breaking while loop easier
    """
    elapsed = 0
    st_interface.connect(wifi_name, wifi_pw)
    time.sleep(1)
    start = time.ticks_ms()
    while not st_interface.isconnected():
        elapsed = time.ticks_ms() - start
        if elapsed > timeout_ms:
            break  # get out of while loop

    return st_interface.isconnected(), elapsed


def datetime_str_to_rtc_tuple(datetime_str, weekday=0):
    """
    create tuple for RTC datetime:
    https://docs.micropython.org/en/latest/library/machine.RTC.html
     (year, month, day, weekday, hours, minutes, seconds, subseconds)
    e.g. 2022-11-11T17:33:50.057884-08:00 --> (2022, 11, 11, 17, 33, 50, )
    """
    date_str, time_str = datetime_str.split('T')
    yr, mo, day = date_str.split('-')
    time_str, offset = time_str.split('-')
    hrs, mins, secs = time_str.split(':')

    secs, frac_secs = secs.split('.')
    frac_secs = frac_secs.split('-')[0]
    return (int(yr), int(mo), int(day), int(weekday), int(hrs), int(mins), int(secs), 0)


def get_iso_datestr_from_rtc(rtc):
    """
    Take tuple from rtc and build ISO datestr
    TODO: what about timezone / offset???
    Args:
        rtc: real time clock object
    Returns: ISO datetime str
    """
    rtc_date_obj = rtc.datetime()
    if rtc_date_obj:
        yr, mo, day, weekday, hrs, mins, secs, msecs = rtc_date_obj
        return f"{yr}-{mo}-{day}T{hrs}:{mins}:{secs}.{msecs}"


def set_rtc_from_internet(rtc):
    """
    Retrieve current west coast time from API,
    parse into tuplce that rtc undestands, then set clock
    Args:
        rtc: real time clock object
    """
    response = urequests.get("http://worldtimeapi.org/api/timezone/America/Los_Angeles").json()
    dt, weekday = response['datetime'], response['day_of_week']
    rtc.datetime(datetime_str_to_rtc_tuple(dt, weekday=weekday))


def blink_led(led, interval=0.5, num_of_blinks=5, is_embedded=False):
    """
    Generic function to blink led pin
    Args:
        led: machine.Pin(PIN#, Pin.OUT) obj
        interval: int, time in secs between blinks
        num_of_blinks: int, num of blinks to perform
        is_embedded: bool, alter how we turn led on/off
    """
    blink_counter = 0
    while blink_counter < num_of_blinks:
        led.on() if is_embedded else led.value(1)
        time.sleep(interval)
        led.off() if is_embedded else led.value(0)
        blink_counter += 1


def start_over(delay_secs):
    """
    Func to reset ESP32 and start over
    Useful if we lose WIFI and need to reconnect
    Args:
        delay_secs: int, seconds to wait between reset
    """
    time.sleep(delay_secs)
    reset()
