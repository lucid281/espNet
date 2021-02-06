# Explore
> Before you begin, make sure to register a device first!

The tree-like nature of the command line (thank you [python-fire](https://github.com/google/python-fire)) lets you tap into the system/device/jobs/etc quickly and easily. You can also access helper classes, like the requests for devices. 

```
./espcli device porch
```
The above command will show you help for the Device object. The section `device porch` returns a 'Device' object for the device registered as `porch`. Some options listed here are used by EspNet internally, like `update`, and others are for user tasks, like adding jobs or sensors.


#### Requests - get_basic
For example, `get_basic` is called every update interval for each device.  `get_basic` is used as a health check and returns a hash with the device id, temp, gpio status, etc. 

Direct access to the requests used by EspNet for device interaction, bypassing locks.
```
./espcli device porch requests get_basic
gpio: {"0": 1, "1": 1, "2": 0, "3": 1, "4": 0, "5": 1, "6": 0, "7": 1, "8": 0, "9": 1, "10": 1, "11": 1, "12": 0, "13": 0, "14": 1, "15": 1, "16": 0, "17": 0, "18": 0, "19": 0, "37": 0, "21": 0, "22": 0, "23": 0, "38": 0, "25": 0, "26": 0, "27": 0, "39": 0, "32": 0, "33": 0, "34": 0, "35": 0, "36": 0}
f:    111
id:   3c71bff93720
```
same call with `curl`:
```
curl -X http://ip.add.re.ss
```

#### Manually Update EspNet and Upload Pending Metrics
An `update` consists of the following actions:
* request a lock for accessing the device
* perform an HTTP GET to the device's site root, `get_basic` (`http://ip.add.re.ss/`)
* results contain device id, temperature and gpio status. commit that data to redis for the device
* committed metric data is added to a redis stream
* periodically send backlogged metrics to datadog.

Try to run this.
```
./espcli device porch get_f
```
`get_f` returns `None` in python land if the device isn't online, so you won't see anything return.

Now try an `update`
```
./espcli device porch update
```
You should have seen the same help as `device porch`, but after a short delay, before I explain this, Now try this:
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