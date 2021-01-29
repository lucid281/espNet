import redis
import requests
import espnet


class SystemRedis:
    keys = espnet.SystemKeys

    def __init__(self, r: redis.Redis):
        self.r = r

    def devices(self):
        return self.r.hgetall(self.keys.ip_list)

    def ids(self):
        return self.r.hgetall(self.keys.ids)

    def register(self, ip, name):
        response = requests.get(f'http://{ip}', timeout=3).json()
        if not {'id', 'f', 'gpio'}.issubset(response.drm()):
            return False
        self.r.hset(self.keys.ids, name, response["id"])
        self.r.hset(self.keys.ip_list, name, ip)

    def unregister(self, name):
        self.r.hdel(self.keys.ids, name)
        self.r.hdel(self.keys.ip_list, name)

    def is_online(self, name):
        return True if self.r.exists(f'devices:{name}:status') > 0 else False
