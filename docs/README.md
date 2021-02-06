
# First Time Setup

1. install `redis`, `picocom`, `pipenv`, `make`
2. configure redis to use a socket @ `/var/run/redis/redis-server.sock`
3. add user to `dialout` and `redis` groups
4. reboot
5. clone this repo, cd to dir
6. `pipenv install`
7. `pipenv shell` youll now have a proper environment to run this
8. init redis consumers: `./espcli init_consumers`

espNet is a python module, call it with `python -m espnet` or as shown above run the `./espcli` script in the repo's root in the proper venv.

## Flash and Test a Device
This as been covered in length: [Getting Micropython for Esp32](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html#getting-the-firmware)

`cd` to the `esp32` folder, modify the `boot.py` to suit your ip space.

copy the webserver files to the esp32 with `make put-app put-boot`

That should be it, reboot the esp32, and it should connect to wifi. Confirm this by going to the device's ip address in your browser with `http://ip.add.re.ss/ui` , obviously replacing `ip.add.re.ss` with the address you used in `boot.py`. You should see a very simple web page with the serial number of the device at the top, followed by `board_temp`.

You can now use this device with this crude UI, via GET, POST commands, or with EspNet.

## DataDog
EspNet expects `DATADOG_API_KEY` and `DATADOG_APP_KEY` env vars to be set before collection.

## Register
Add a device to EspNet `./espcli register IP NAME`, replacing IP and NAME respectively. 

List all devices: `./espcli devices`, explore a single device `./espcli device NAME`
