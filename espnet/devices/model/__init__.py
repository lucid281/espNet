import redis
from redlock import Redlock
import espnet


class DeviceStatus:
    def __init__(self, device):
        self._device = device

    def __bool__(self):
        return True if self._device.get_f() else False

    def __repr__(self):
        return str(self.__bool__())


class DeviceKeys:
    system = espnet.SystemKeys
    expire = 15

    def __init__(self, name):
        self.status = f'devices:{name}:status'
        self.gpio_hash = f'devices:{name}:gpio_status'
        self.dev_temp = f'devices:{name}:f'

        self.locks = f'devices:{name}:locks'
        self.jobs = f'devices:{name}:jobs'
        self.dht22 = f'devices:{name}:dht22'
        self.adc_data = f'devices:{name}:adc'


class DeviceRedis:
    keys = DeviceKeys

    def __init__(self, r: redis.Redis, name):
        self.keys = self.keys(name)
        self.r = r
        self._locks = Redlock([r])
        self._name = name
        self.status = DeviceStatus(self)

    def get_uid(self):
        return self.r.hget(self.keys.system.ids, self._name)

    def set_gpio(self, gpio_response: dict):
        gpio = {str(k): str(v) for k, v in gpio_response.items()}
        self.r.hset(self.keys.gpio_hash, mapping=gpio)
        self.r.expire(self.keys.gpio_hash, self.keys.expire)
        return gpio

    def get_gpio(self):
        return {int(k): int(v) for k, v in self.r.hgetall(self.keys.gpio_hash).items()}

    def set_f(self, f):
        f = float(f)
        self.r.set(self.keys.dev_temp, float(f), ex=self.keys.expire)
        return f

    def get_f(self):
        temp = self.r.get(self.keys.dev_temp)
        return float(temp) if temp else None

    def set_lc(self, time):
        t = str(int(time))
        self.r.set(self.keys.status, t, ex=self.keys.expire)
        return t

    def lock(self, purpose, ttl=1000):
        return self._locks.lock(f'{self.keys.locks}:{purpose}', ttl=ttl)

    def unlock(self, lock):
        return self._locks.unlock(lock)

    def jobs(self):
        return {i: self.r.hgetall(f'{self.keys.jobs}:{i}') for i in
                self.r.smembers(self.keys.jobs)}

    def add_timer_job(self, name, pin, start, hours):
        d = {"pin": pin,
             "start": start,
             "duration": int(hours * 60 * 60),
             "type": "timer",
             }
        self.r.sadd(self.keys.jobs, name)
        self.r.hset(f'{self.keys.jobs}:{name}', mapping=d)

    def add_threshold_job(self, name, pin, start, hours, lock, input_key, target):
        d = {"pin": pin,
             "start": start,
             "duration": int(hours * 60 * 60),
             "type": "threshold",
             "lock": lock,
             "input": input_key,
             "target": target,
             }
        self.r.sadd(self.keys.jobs, name)
        self.r.hset(f'{self.keys.jobs}:{name}', mapping=d)
