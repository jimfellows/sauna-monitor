from machine import Pin, SoftI2C, unique_id
import utime
import network
import time
import auth_urequests as urequests
import os
import ntptime

POLYNOMIAL = 0x131  # P(x) = x^8 + x^5 + x^4 + 1 = 100110001
MEASURE_CMD = b'\x2C\x10'
STATUS_CMD = b'\xF3\x2D'
RESET_CMD = b'\x30\xA2'
CLEAR_STATUS_CMD = b'\x30\x41'
ENABLE_HEATER_CMD = b'\x30\x6D'
DISABLE_HEATER_CMD = b'\x30\x66'


def _check_crc(data):
    # calculates 8-Bit checksum with given polynomial
    crc = 0xFF

    for b in data[:-1]:
        crc ^= b;
        for _ in range(8, 0, -1):
            if crc & 0x80:
                crc = (crc << 1) ^ POLYNOMIAL;
            else:
                crc <<= 1
    crc_to_check = data[-1]
    return crc_to_check == crc


def send_cmd(i2c, cmd_request, response_size=6, read_delay_ms=100):
    """
    Send a command to the sensor and read (optionally) the response
    The responsed data is validated by CRC
    """
    try:
        i2c.start();
        i2c.writeto(68, cmd_request);
        if not response_size:
            i2c.stop();
            return
        utime.sleep_ms(read_delay_ms)
        data = i2c.readfrom(68, response_size)
        i2c.stop();
        utime.sleep(1)
        for i in range(response_size // 3):
            if not _check_crc(data[i * 3:(i + 1) * 3]):  # pos 2 and 5 are CRC
                raise Exception('OH NO')
        if data == bytearray(response_size):
            raise Exception('OH NO')
        return data
    except Exception as ex:
        if 'I2C' in ex.args[0]:
            raise Exception('OH NO')
        raise ex


def measure_int(i2c, raw=False):
    """
    Get the temperature (T) and humidity (RH) measurement using integers.
    If raw==True returns a bytearrya(6) with sensor direct measurement otherwise
    It returns a tuple with 4 values: T integer, T decimal, H integer, H decimal
    For instance to return T=24.0512 and RH= 34.662 This method will return
    (24, 5, 34, 66) Only 2 decimal digits are returned, .05 becomes 5
    Delta values are not applied in this method
    The units are Celsius and percent.
    """

    data = send_cmd(i2c, MEASURE_CMD, 6);
    if raw:
        return data
    aux = (data[0] << 8 | data[1]) * 175
    t_int = (aux // 0xffff) - 45;
    t_dec = (aux % 0xffff * 100) // 0xffff
    aux = (data[3] << 8 | data[4]) * 100
    h_int = aux // 0xffff
    h_dec = (aux % 0xffff * 100) // 0xffff

    return t_int, t_dec, h_int, h_dec


print("Starting script")

blinks = 0
led = Pin(2, Pin.OUT)
while blinks < 3:
    led.on()
    utime.sleep(0.1)
    led.off()
    utime.sleep(0.1)
    blinks += 1

# set up leds to flash based on whats happening
pending_led = Pin(18, Pin.OUT)
# pending_led.value(1)
success_led = Pin(19, Pin.OUT)
error_led = Pin(21, Pin.OUT)

pending_led.value(1)

print("Getting data from temp sensor")
scl_pin = Pin(23)
sda_pin = Pin(22)
i2c = SoftI2C(scl=scl_pin, sda=sda_pin, freq=400000)
temp_data = measure_int(i2c)

# connect to wifi if not already
print("connecting to WIFI")
station = network.WLAN(network.STA_IF)
station.active(True)
if not station.isconnected():
    station.connect("Jamnet24", "maggiejo")

device = {
    'model': 'ESP-WROOM-32',
    'unique_id': unique_id(),
    'sysname': os.uname().sysname,
    'release': os.uname().release
}

sensor_data = {
    "temp_c": str(temp_data[0]) + '.' + str(temp_data[1]),
    "humidity_rel": str(temp_data[2]) + '.' + str(temp_data[3]),
    'device_model': 'ESP-WROOM-32',
    'device_id': str(unique_id()),
    'device_release': os.uname().release,
    'unix_dt': ntptime.time()
    # 'unix_dt': ntptime.localtime()  # this needs to be fixed
}

try:
    doc_post = urequests.post('http://192.168.1.101:5984/home-sensors', json=sensor_data, auth=["admin", "admin"])
    print(doc_post.status_code)
except Exception as e:
    print(str(e))

pending_led.value(0)
if str(doc_post.status_code) == '201':
    success_led.value(1)
    time.sleep(3)
    success_led.value(0)

else:
    error_led.value(1)
    time.sleep(3)
    error_led.value(0)
