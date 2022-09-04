# sauna-monitor

Code to record and view temperature of the sauna I have in my backyard.
The stove is wood fired and I need a way to see when the sauna is ready
without having to walk out in the cold to check it.

General idea is to have an ESP32 board connected to a temperature and 
humidity sensor.  This board will be powered by a standard outlet and wake up at a defined interval, take
a sensor reading, and submit them over WiFi to either a local server or the cloud (TBD).

A basic PWA will allow me to review the current sensor readings on my phone, tablet
or laptop.  Push notifications might be nice as well.

## Hardware Setup

### ESP32
I'm using the [ESP-WROOM-32](https://www.amazon.com/ESP-WROOM-32-Development-Microcontroller-Integrated-Compatible/dp/B08D5ZD528/ref=sr_1_3?keywords=ESP32&qid=1662211333&sr=8-3) witth micropython installed.

Steps to flash firmware:

1. Download the latest micropython distribution for ESP32 at https://micropython.org/download/esp32/
2. Under my root python, install [esptool](https://docs.espressif.com/projects/esptool/en/latest/esp32/):
 
`pip install esptool`

3. While holding down the boot button on my ESP32 (not sure this was necessary), I first erased any existing flash:

`python -m esptool --chip esp32 erase_flash`

4. Again while holding down boot, flash the downloaded bin file:

`python -m esptool --chip esp32 --port COM3 write_flash -z 0x1000 esp32-20220618-v1.19.1.bin`

### Temperature and Humidity Sensor

I wanted a somewhat weather proof sensor for the sauna.  I purchased the Taidacent SHT30 Sensor from [Amazon](https://www.amazon.com/gp/product/B07F9X9Q37/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1).
So far its working great in my office.  Wire configurations are as follows:

* Blue wire: Data (SDA)
* Yellow wire: Clock (SCL)
* Red wire: Power (VDD)
* Green wire: Ground (VSS)

### Wiring Diagram
Coming soon

## Database

For now I'm using a local instance of [CouchDB](https://docs.couchdb.org/en/stable/).  
Couch allows me to push documents using basic HTTP requests, which is nice when
using basic micropython libraries.  Eventually I hope to push this to a local server, and may then synchronize to the cloud.  Or, write data
directly to the cloud.

To spin up a local CouchDB in [Docker](https://hub.docker.com/_/couchdb):

`docker run -d --name couchdb -p 5984:5984 -e COUCHDB_USER=admin -e COUCHDB_PASSWORD=admin -v /usr/share/couchdb/data:/opt/couchdb/data --restart unless-stopped couchdb:latest`

## PWA
Coming soon