import traceback
import redis
import requests
import simplejson
import logging as log
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .model import DeviceRedis
from .requests import DeviceRequests


class Device(DeviceRedis):
    def __init__(self, r: redis.Redis, name: str, ip: str, online: bool):
        super().__init__(r, name)
        self.ip = ip
        self.name = name
        self.online = online
        self.requests = DeviceRequests(self.ip)

        # amount of time to keep data alive in redis.
        self._redis_expire = 15

    def __repr__(self):
        return f'<Device: {self.name}>'

    def update(self, skip_lock=True, **kwargs):
        # wait for interval lock to expire before collecting
        interval = kwargs.get('device_update_interval', 5)
        if not skip_lock:
            if not self.lock('interval', interval * 1000):
                return False  # break out of loop, only collect after lock expires.

        # give requests 2x device_update_interval to recover
        r_lock = self.lock('request', (interval * 2) * 1000)
        if not r_lock:
            if skip_lock:
                print('devices request lock active, devices probably busy.')
            return False  # a previous request slow or failed

        # issue request, handle certain exceptions, update self and redis
        failed = None
        try:
            response = self.requests.get_basic(timeout=kwargs.get("device_requests_timeout"))
            if not {'id', 'f', 'gpio'}.issubset(response.keys()):
                raise KeyError("Device response is missing certain keys!")
            if not self.get_uid() == response["id"]:
                raise NameError("Device id does not match registered id!")

            gpio = self.set_gpio(response["gpio"])
            f = self.set_f(response["f"])
            lc = self.set_lc(datetime.now().timestamp())

            if self.r.exists(self.keys.dht22):
                self.update_dht22()

            self.commit_metric(**{'metric': 'esp32.f',
                                  'type': 'gauge',
                                  'points': [(lc, f)],
                                  'tags': [f'name:{self.name}']})

            for job_name, job in self.jobs().items():
                self.commit_metric(**{'metric': 'esp32.gpio',
                                      'type': 'gauge',
                                      'points': [(lc, gpio[job["pin"]])],
                                      'tags': [f'name:{self.name}', f'pin:{job["pin"]}', f'job:{job_name}']
                                      })
            self.unlock(r_lock)
            return self
        except requests.exceptions.ConnectTimeout:
            failed = traceback.format_exc().splitlines()
        except requests.exceptions.ConnectionError:
            failed = traceback.format_exc().splitlines()
        except simplejson.errors.JSONDecodeError:
            failed = traceback.format_exc().splitlines()
        except requests.exceptions.ReadTimeout:
            failed = traceback.format_exc().splitlines()
        if failed:
            log.warning(f'{self.name} get_gpio failed with: {failed[-1]}')
            return False  # this update has failed

    def add_dht22(self, name, pin):
        self.r.hset(self.keys.dht22, name, pin)

    def update_dht22(self, **kwargs):
        for name, pin in self.list_dht22().items():
            r = self.requests.get_dht22(pin, timeout=kwargs.get("device_requests_timeout", 2))
            k = f'{self.keys.dht22}:{name}'
            self.r.set(f'{k}:temp', r['temp'], ex=self._redis_expire)
            self.r.set(f'{k}:humidity', r['humidity'], ex=self._redis_expire)
            self.commit_metric(**{'metric': 'esp32.dht22.temp',
                                  'type': 'gauge',
                                  'points': [(self.lc, 1.8 * float(r['temp']) + 32)],
                                  'tags': [f'name:{self.name}', f'pin:{pin}', f'sensor:{name}']
                                  })
            self.commit_metric(**{'metric': 'esp32.dht22.humidity',
                                  'type': 'gauge',
                                  'points': [(self.lc, float(r['humidity']))],
                                  'tags': [f'name:{self.name}', f'pin:{pin}', f'sensor:{name}']
                                  })

    def list_dht22(self):
        return self.r.hgetall(self.keys.dht22)

    def get_dht22(self):
        s = {}
        for name, pin in self.list_dht22().items():
            _ = f'{self.keys.dht22}:{name}'
            s[name] = {"temp": self.r.get(f'{_}:temp'), "humidity": self.r.get(f'{_}:humidity')}
        return s

    def commit_metric(self, **kwargs):
        self.r.xadd(self.keys.system.stream_key, {k: simplejson.dumps(v) for k, v in kwargs.items()}, maxlen=5000)

    def sync_job_state(self, **kwargs):
        jobs = self.jobs()
        if not self.online or not jobs:
            return False  # no gpio or no jobs

        inactive = set()
        current_gpio = self.get_gpio()
        for job_name, job in jobs.items():
            pin = int(job['pin'])
            if self._timer_is_active(job):
                if job['type'] == 'timer':
                    if current_gpio[pin] == 0:
                        self.requests.set_gpio(pin, 1, timeout=kwargs.get("device_requests_timeout", 2))
                elif job['type'] == 'threshold':
                    self._threshold_job(current_gpio, job)
            else:
                inactive.add(pin)

        if len(jobs) == len(inactive):  # we have jobs but none are active.
            for job_name, job in jobs.items():
                pin = int(job['pin'])
                if pin in inactive and current_gpio[pin] == 1:
                    self.requests.set_gpio(pin, 0, timeout=kwargs.get("device_requests_timeout", 2))

    @staticmethod
    def _timer_is_active(job: dict):
        hour, minute, second = job['start'].split(":")
        hour, minute, second = int(hour), int(minute), int(second)
        timer_duration = int(job['duration'])

        now = datetime.now()
        yesterday = now + relativedelta(days=-1)
        today = now.replace(hour=hour, minute=minute, second=second)

        if today < now < today + relativedelta(seconds=timer_duration):
            return True
        elif yesterday.replace(hour=hour, minute=minute, second=second) + relativedelta(seconds=timer_duration) > now:
            return True
        return False

    def _threshold_job(self, current_gpio: dict, job: dict):
        pin = int(job['pin'])
        input_key = job['input']  # source data
        lock_time = int(job['lock'])  # max time between interactions
        target = float(job['target'])

        pin_lock = self.lock(f'pin:{pin}', lock_time)
        if not pin_lock:
            return False

        if not self.r.exists(input_key):
            return False

        data = float(self.r.get(input_key))
        data = 1.8 * data + 32

        if data > target and current_gpio[pin] == 1:  # data is high and pin is 'on', turn off
            if not self.requests.set_gpio(pin, 0):
                self.unlock(pin_lock)  # essentially a retry
        elif data < target and current_gpio[pin] == 0:  # data is low, pin is off, turn on
            if not self.requests.set_gpio(pin, 1):
                self.unlock(pin_lock)  # essentially a retry
