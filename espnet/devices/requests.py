import requests

GET = 'GET'
POST = 'POST'


class DeviceRequests:
    def __init__(self, site_root):
        self._session = requests.Session()
        self.site_root = site_root

    def _request(self, method, **kwargs) -> dict:
        return self._session.request(**{"method": method, **kwargs}).json()

    def _base(self, url=None, **kwargs):
        return {"url": f'http://{self.site_root}' if not url else f'http://{self.site_root}/{url}',
                "timeout": kwargs.get("device_requests_timeout", 2)}

    def get_basic(self, **kwargs):
        return self._request(GET, **self._base(**kwargs))

    def set_gpio(self, pin, value, **kwargs):
        request = {**self._base('/gpio', **kwargs),
                   "data": {"pin": int(pin),
                            "value": value}}
        return self._request(POST, **request)

    def flip_gpio(self, pin, **kwargs):
        request = {**self._base('/gpio', **kwargs),
                   "data": {"pin": int(pin),
                            "value": 2}}
        return self._request(POST, **request)

    def get_dht22(self, pin, **kwargs):
        request = {**self._base('/dht22', **kwargs),
                   "data": {"read_pin": int(pin)}}
        return self._request(POST, **request)