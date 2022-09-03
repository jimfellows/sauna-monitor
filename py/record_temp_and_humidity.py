from sht30 import SHT30

sht30 = SHT30(scl_pin=23, sda_pin=18)
sht30.init()
sensor_data = sht30.measure_int()
print(sensor_data)
