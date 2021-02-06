# Explore
The tree-like nature of the command line (thank you [python-fire](https://github.com/google/python-fire)) lets you tap into the system/device/jobs/etc quickly and easily. You can also access helper classes, like prepared requests for devices, used other places in code.

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