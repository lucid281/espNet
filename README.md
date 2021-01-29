# EspNet
EspNet is lightweight microcontroller management and data logging application. Built with Python, Redis, REST, MicroPython and Datadog.

Flash your esp32 with EspNet's web server (written in micropython!). This transforms each Esp32 into a device that can be controlled standalone or with EspNet. Each Esp32 device has its own web GUI, great for testing or using solo!

Once a device is online, you can register it with EspNet. Once registered, the device's temperature will start reporting to Datadog based. Now you can configure EspNet with various sensors, collection intervals and that data will be reported to Datadog immediately. Then add jobs to maintain gpio state based on timers or thresholds.


**Features:**

* powerful command line centric app
* configure simple jobs to maintain pin state
  * if device resets and comes back online, pin state will be corrected.
  * timer -- turn on pin and hold
  * threshold -- if value of a Redis key > target, turn off pin, if < target, turn on
* tune primary loop intervals for reaction speed or resource consumption
    * faster loops == faster reaction to cool-downs
* lock mechanisms to prevent simultaneous calls/actions on a device
  * locks always timeout, so I use them for cool-down for intervals
  * creates a stable networking environment
    * lock enables 1 HTTP session per device across the app
        * timeouts == device won't perma-lock a device

# Status
Operationally it's the Esp32 modules and EspNet are reliable enough for production, it can tolerate the failures I've discovered and keep humming along. 

However, the code base is still evolving, and I would not consider EspNet stable enough to be used as a module.

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

## Explore
The nested nature of the command line (thank you [fire](fire)) lets you tap into the system/device/jobs/etc quickly and easily. You can also access helper classes, like prepared requests for devices, used other places in code.

For example, 'get_basic' is called every update interval for each device, making the HTTP request and returning a hash with the device id, temp and gpio status. 

#### Requests - get_basic
Direct access to the requests used for a device directly, bypassing locks.
```
./espcli device porch requests get_basic
gpio: {"0": 1, "1": 1, "2": 0, "3": 1, "4": 0, "5": 1, "6": 0, "7": 1, "8": 0, "9": 1, "10": 1, "11": 1, "12": 0, "13": 0, "14": 1, "15": 1, "16": 0, "17": 0, "18": 0, "19": 0, "37": 0, "21": 0, "22": 0, "23": 0, "38": 0, "25": 0, "26": 0, "27": 0, "39": 0, "32": 0, "33": 0, "34": 0, "35": 0, "36": 0}
f:    111
id:   3c71bff93720
```

#### Manually Update EspNet and Upload Pending Metrics
An `update` consists of the following actions:
* request a lock for accessing the device
* perform an HTTP GET to the device's site root (`http://ip.add.re.ss/`)
* results contain device id, temperature and gpio status, commit that data to redis device keys
* committed metric data is also added to a redis stream and batch processed later

```
./espcli device porch
```
The above command will show you help for the Device object. The section `device porch` returns a Device object for the device 'porch', which we then call `update` on, which then returns the Device object again so that we can make another call. 

```
./espcli device porch update
```
You should have seen the same help for 'porch' after a short delay. Now try this:
```
./espcli device porch update - get_f
112.0
```
This should update again, but this time return the device temp. Notice the `-`, this tells the `fire` module to resolve the previous object before calling `get_f`

During all this, EspNet has been keeping track of the device temp in a redis stream. Check the entries in the stream:

```
./espcli xinfo
{'length': 476, 'radix-tree-keys': 9, 'radix-tree-nodes': 21, 'groups': 1, 'last-generated-id': '1611959408459-0', 'first-entry': ('1611346857308-0', {'metric': '"esp32.f"', 'type': '"gauge"', 'points': '[["1611346857", 100.0]]', 'tags': '["name:porch"]'}), 'last-entry': ('1611959408459-0', {'metric': '"esp32.f"', 'type': '"gauge"', 'points': '[["1611959408", 112.0]]', 'tags': '["name:porch"]'})}
[{'name': 'root', 'pending': 0, 'idle': 516767930}]
[{'name': 'datadog', 'consumers': 1, 'pending': 0, 'last-delivered-id': '1611443106570-0'}]
```
Notice the very high `idle` and the old `last-delivered-id` (stream ids == timestamp)

run `upload_queued_metrics`

```
./espcli upload_queued_metrics
3
```
Now look in DataDog for your device under your hostname. 