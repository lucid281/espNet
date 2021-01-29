import os
import threading
from datetime import timedelta

from timeloop import Timeloop

import espnet


def update_device(**kwargs):
    name = kwargs.pop('name')
    dev = espnet.EspNetSystem().device(name)
    dev.update(skip_lock=False)


def sync_device_job(**kwargs):
    name = kwargs.pop('name')
    dev = espnet.EspNetSystem().device(name)
    dev.sync_job_state(**kwargs)


def upload_metrics():
    sys = espnet.EspNetSystem()
    sys.upload_queued_metrics()


class EspNetDaemon:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs["kwargs"]
        self.heartbeat = 1 / self.kwargs.pop('heartbeat')
        self.redis_url = os.environ.get('REDIS_URL')

    def start(self):
        tl = Timeloop()

        @tl.job(interval=timedelta(seconds=self.heartbeat))
        def update_devices():
            sys = espnet.EspNetSystem()
            devices = []
            for name in sys.devices().keys():
                devices.append(
                    threading.Thread(
                        target=update_device,
                        kwargs={"name": name, **self.kwargs},
                    )
                )
            [i.start() for i in devices]
            [i.join(10) for i in devices]

        @tl.job(interval=timedelta(seconds=self.heartbeat))
        def sync_device_jobs():
            sys = espnet.EspNetSystem()
            j = []
            for name in sys.devices().keys():
                j.append(
                    threading.Thread(
                        target=sync_device_job,
                        kwargs={"name": name, **self.kwargs},
                    )
                )
            [i.start() for i in j]
            [i.join(10) for i in j]

        @tl.job(interval=timedelta(seconds=self.kwargs.get("metric_upload_interval")))
        def upload_queued_metrics():
            j = [threading.Thread(target=upload_metrics)]
            [i.start() for i in j]
            [i.join(10) for i in j]

        tl.start(block=True)
