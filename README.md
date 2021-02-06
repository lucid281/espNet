# EspNet
EspNet is lightweight microcontroller management and data logging application. Built with Python, Redis, REST, MicroPython and Datadog.

Flash your esp32 with EspNet's web server (written in micropython!). EspNet's configuration-less endpoint is identified by a built-in hardware ID.  Devices can be controlled standalone or with EspNet. Each Esp32 device has its own web GUI, great for testing or using solo!

Once a device is on your network and registered with EspNet, the device's temperature will start reporting to Datadog. Now you can configure EspNet with various sensors, collection/reporting intervals. Then add jobs to maintain gpio state based on timers or thresholds.


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

# Project Status: Public Alpha
Operationally the Esp32 modules and EspNet are reliable enough for production, it can tolerate the failures I've discovered and keep humming along. Reliable power is important, and the source of most reliability issues.

However, the code base is still evolving, and I would not consider EspNet stable enough to be used as a module.


# Documentation
[Full docs here.](docs/README.md)
