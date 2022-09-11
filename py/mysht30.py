
import time
from machine import Pin, SoftI2C

# I2C address B 0x45 ADDR (pin 2) connected to VDD
DEFAULT_I2C_ADDRESS = 0x45

class MySht30:
    """
    Based on class written by Roberto S鐠嬶箯chez, see https://github.com/rsc1975/micropython-sht30/blob/master/sht30.py
    SHT30 sensor driver in pure python based on I2C bus

   References:
   * https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/2_Humidity_Sensors/Sensirion_Humidity_Sensors_SHT3x_Datasheet_digital.pdf
   * https://www.wemos.cc/sites/default/files/2016-11/SHT30-DIS_datasheet.pdf
   * https://github.com/wemos/WEMOS_SHT3x_Arduino_Library
   * https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/11_Sample_Codes_Software/Humidity_Sensors/Sensirion_Humidity_Sensors_SHT3x_Sample_Code_V2.pdf
   """

    POLYNOMIAL = 0x131  # P(x) = x^8 + x^5 + x^4 + 1 = 100110001
    MEASURE_CMD = b'\x2C\x10'
    STATUS_CMD = b'\xF3\x2D'
    RESET_CMD = b'\x30\xA2'
    CLEAR_STATUS_CMD = b'\x30\x41'
    ENABLE_HEATER_CMD = b'\x30\x6D'
    DISABLE_HEATER_CMD = b'\x30\x66'

    def __init__(self, scl_pin_num=23, sda_pin_num=22, delta_temp=0, delta_hum=0):
        self._current_data = None
        self.scl_pin = Pin(scl_pin_num)
        self.sda_pin = Pin(sda_pin_num)
        self.i2c = SoftI2C(scl=self.scl_pin, sda=self.sda_pin)
        self.i2c_address = self.i2c.scan()[0]
        time.sleep_ms(50)

    def _check_crc(self, data):
        # calculates 8-Bit checksum with given polynomial
        crc = 0xFF

        for b in data[:-1]:
            crc ^= b;
            for _ in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ self.POLYNOMIAL
                else:
                    crc <<= 1
        crc_to_check = data[-1]
        return crc_to_check == crc

    def send_cmd(self, cmd_request, response_size=6, read_delay_ms=100):
        """
        Send a command to the sensor and read (optionally) the response
        The responsed data is validated by CRC
        """
        try:
            self.i2c.start();
            self.i2c.writeto(self.i2c_address, cmd_request);
            if not response_size:
                self.i2c.stop()
                return
            time.sleep_ms(read_delay_ms)
            data = self.i2c.readfrom(self.i2c_address, response_size)
            self.i2c.stop()
            for i in range(response_size // 3):
                if not self._check_crc(data[i * 3:(i + 1) * 3]):  # pos 2 and 5 are CRC
                    raise Exception('OH NO')
            if data == bytearray(response_size):
                raise Exception('OH NO')
            return data
        except Exception as ex:
            if 'I2C' in ex.args[0]:
                raise Exception('OH NO')
            raise ex

    def measure_int(self, raw=False):
        """
        Get the temperature (T) and humidity (RH) measurement using integers.
        If raw==True returns a bytearrya(6) with sensor direct measurement otherwise
        It returns a tuple with 4 values: T integer, T decimal, H integer, H decimal
        For instance to return T=24.0512 and RH= 34.662 This method will return
        (24, 5, 34, 66) Only 2 decimal digits are returned, .05 becomes 5
        Delta values are not applied in this method
        The units are Celsius and percent.
        """

        data = self.send_cmd(self.MEASURE_CMD, 6);
        if raw:
            return data
        aux = (data[0] << 8 | data[1]) * 175
        t_int = (aux // 0xffff) - 45;
        t_dec = (aux % 0xffff * 100) // 0xffff
        aux = (data[3] << 8 | data[4]) * 100
        h_int = aux // 0xffff
        h_dec = (aux % 0xffff * 100) // 0xffff


        self._current_data = t_int, t_dec, h_int, h_dec
        return t_int, t_dec, h_int, h_dec

    @staticmethod
    def celsius_to_fahrenheit(c):
        return c * 1.8 + 32

    @property
    def current_temp_c(self):
        try:
            return float(str(self._current_data[0]) + '.' + str(self._current_data[1]))
        except Exception as e:
            print(str(e))
            return

    @property
    def current_temp_f(self):
        return self.celsius_to_fahrenheit(self.current_temp_c)

    @property
    def current_data(self):
        return self._current_data

    @property
    def current_humidity(self):
        try:

            return float(str(self._current_data[2]) + '.' + str(self._current_data[3]))
        except Exception as e:
            print(str(e))
            return


class SHT30Error(Exception):
    """
    Custom exception for errors on sensor management
    """
    BUS_ERROR = 0x01
    DATA_ERROR = 0x02
    CRC_ERROR = 0x03

    def __init__(self, error_code=None):
        self.error_code = error_code
        super().__init__(self.get_message())

    def get_message(self):
        if self.error_code == SHT30Error.BUS_ERROR:
            return "Bus error"
        elif self.error_code == SHT30Error.DATA_ERROR:
            return "Data error"
        elif self.error_code == SHT30Error.CRC_ERROR:
            return "CRC error"
        else:
            return "Unknown error"


