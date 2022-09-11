# This file is executed on every boot (including wake-boot from deepsleep)

# import esp
from mysht30 import MySht30
from machine import Pin, unique_id, deepsleep
import time
import network
import auth_urequests as urequests
import os

print("ESP32 booted, starting script")

# set up leds to flash based on whats happening
embedded_led = Pin(2, Pin.OUT)
pending_led = Pin(18, Pin.OUT)
success_led = Pin(19, Pin.OUT)
error_led = Pin(21, Pin.OUT)

# initial blinks so we know we're starting
start_blinks = 0
while start_blinks < 3:
    embedded_led.on()
    time.sleep(0.1)
    embedded_led.off()
    time.sleep(0.1)
    start_blinks += 1

pending_led.value(1)
time.sleep(2)

# start big try/except statement
try:
    # start connection to wifi attempt
    station = network.WLAN(network.STA_IF)
    station.active(True)

    if not station.isconnected():
        print("Connecting to WiFi")
        station.connect("MYWIFI", "MYWIFIPW")
        conn_timeout_ms = 10000
        conn_start_time = time.ticks_ms()
        while not station.isconnected():
            now = time.ticks_ms()
            duration = now - conn_start_time
            if duration > conn_timeout_ms:
                raise Exception('Unable to connect to WIFI')
    
    print("Connected to WiFi! Continuing with script")
                
    # get datetime from API, rather than mess with RTC
    print("Getting datetime from API")
    dt_response = urequests.get("http://worldtimeapi.org/api/timezone/America/Los_Angeles")
    time.sleep(1)
    dt = dt_response.json()['datetime']
    print(f"Datetime: {dt}")

    # start temp sensor stuff
    print("Taking measurement with sensor")
    sensor = MySht30()
    sensor.measure_int()  # take measurement, sets _current_data
    device_info = os.uname()

    data = {
        'tempF': sensor.current_temp_f,
        'humRel': sensor.current_humidity,
        'dt': dt,
        'loc': 'sauna',
        'deviceModel': device_info.sysname,
        'deviceId': str(unique_id()),
        'deviceRelease': device_info.release,
    }
    
    print(f"Data retrieved, sending to couch")
    print(data)
    print("Posting to couch")
    # send off to couch
    doc_post = urequests.post('http://192.168.1.101:5984/home-sensors', json=data, auth=["COUCHUSER", "COUCHPW"])
    if doc_post.status_code in [201, 200]:
        print("Doc successfully posted!")
        success_led.value(1)
        pending_led.value(0)
        time.sleep(3)
        
    else:
        print(f"Error posting, status code {doc_post.status_code}")
        error_led.value(1)
        time.sleep(3)

except Exception as e:
    pending_led.value(0)
    error_blinks = 0
    print(str(e))
    while error_blinks < 10:
        error_led.value(1)
        time.sleep(0.2)
        error_led.value(0)
        time.sleep(0.2)
        error_blinks += 1
    if station.isconnected():
      urequests.post('http://192.168.1.101:5984/home-sensors', json={'exc': str(e)}, auth=["admin", "admin"])

finally:
    embedded_led.off()
    pending_led.value(0)
    success_led.value(0)
    error_led.value(0)

    deepsleep(150000)

