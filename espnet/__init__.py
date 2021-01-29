from .keys.system import SystemKeys
from .system import EspNetSystem
from .devices import Device
from .run import EspNetDaemon


def get_device_from_name(device_name):
    sys = EspNetSystem()
    d = sys.devices()
    if device_name not in d:
        raise NameError(f'Device, {device_name}, has not been registered.')

    return Device(r=sys.r, name=device_name, ip=d[device_name], online=sys.is_online(device_name))

