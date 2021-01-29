import datetime
import os

import datadog
import redis
from redis import from_url as redis_from_url
import simplejson
from datadog.api import exceptions

import espnet
from .model import SystemRedis


class EspNetSystem(SystemRedis):
    """
    Main application entry point.
    """

    def __init__(self):
        r = redis_from_url(os.environ.get('REDIS_URL'), decode_responses=True)
        super().__init__(r)

    def device(self, name):
        return espnet.get_device_from_name(name)

    def is_online(self, name):
        if name not in self.devices():
            print(f'Device, {name}, has not been registered.')
            exit(1)
        return super().is_online(name)

    def run(self,
            heartbeat,  # internal refresh rate, N per second
            device_update_interval=10,  # collect devices every N seconds
            device_requests_timeout=2,  # requests socket timeout
            device_requests_return=1,  # base expected RTT for a request to a device
            metric_upload_interval=15,  # send metrics every N seconds
            device_update_duration=1,  # time in seconds a device is expected to return
            ):
        kwargs = locals()
        kwargs.pop('self')

        d = espnet.EspNetDaemon(kwargs=kwargs)
        return d.start()

    def init_consumers(self):
        try:
            return self.r.xgroup_create(self.keys.stream_key, self.keys.group_key, '$', True)
        except redis.exceptions.ResponseError:
            return True

    def upload_queued_metrics(self):
        to_do = []
        ids = []
        for stream, data in self.r.xreadgroup(groupname=self.keys.group_key,
                                              consumername=self.keys.metric_consumer,
                                              streams={self.keys.stream_key: '>'},
                                              count=50):
            if self.keys.stream_key == stream:
                for _id, metrics in data:
                    to_do.append(metrics)
                    ids.append(_id)

        if self.send_to_datadog(to_do):
            return self.r.xack(self.keys.stream_key, self.keys.group_key, *ids)

    def send_to_datadog(self, to_do):
        try:
            datadog.initialize()
            return datadog.api.Metric.send(
                metrics=[{k: simplejson.loads(v) for k, v in i.items()} for i in to_do]) if to_do else None
        except exceptions.HttpTimeout:
            print(f"[{datetime.datetime.now().isoformat()}] HTTP Timeout reporting metrics to Datadog, skipping.")
            return False

    def xreadg(self):
        return self.r.xreadgroup(groupname=self.keys.group_key,
                                 consumername=self.keys.metric_consumer,
                                 streams={self.keys.stream_key: '>'},
                                 count=20)

    def xreadgall(self):
        x = self.r.xreadgroup(groupname=self.keys.group_key,
                              consumername=self.keys.metric_consumer,
                              streams={self.keys.stream_key: '0'},
                              count=10)
        for stream, time_series_data, in x:
            for timestamp, encoded_dict in time_series_data:
                print(timestamp, encoded_dict)

    def xack(self, args):
        return self.r.xack(self.keys.stream_key, self.keys.group_key, *args)

    def xpending(self):
        xpending = self.r.xpending(self.keys.stream_key, self.keys.group_key)
        pending, min, max, consumers = xpending['pending'], xpending['min'], xpending['max'], xpending['consumers']

        print(xpending)
        if int(pending) > 0:
            pending_messages = self.r.xpending_range(self.keys.stream_key, self.keys.group_key, min, max, pending,
                                                     self.keys.metric_consumer)
            print(pending_messages)

    def xinfo(self):
        stream = self.r.xinfo_stream(self.keys.stream_key)
        print(stream)
        consumers = self.r.xinfo_consumers(self.keys.stream_key, self.keys.group_key)
        print(consumers)
        groups = self.r.xinfo_groups(self.keys.stream_key)
        print(groups)

    def xclaim(self, idle, ts):
        return self.r.xclaim(self.keys.stream_key, self.keys.group_key, self.keys.metric_consumer, idle, [ts])

    def process_backlog(self, since_delivered):
        # xpending = self.r.xpending(self.keys.stream_key, self.keys.group_key)
        # pending, min, max, consumers = xpending['pending'], xpending['min'], xpending['max'], xpending['consumers']
        xpending = None
        consumers = self.r.xinfo_consumers(self.keys.stream_key, self.keys.group_key)
        to_do = []
        for consumer in consumers:
            if consumer["pending"] > 0:
                xpending = self.r.xpending(self.keys.stream_key, self.keys.group_key) if not xpending else xpending
                pending, _min, _max, _consumers = xpending['pending'], xpending['min'], xpending['max'], xpending[
                    'consumers']
                pending = self.r.xpending_range(name=self.keys.stream_key, groupname=self.keys.group_key,
                                                min=_min, max=_max, count=pending, consumername=consumer["name"])
                pending = [i for i in pending if i["time_since_delivered"] > since_delivered]
                if len(pending) > 0:
                    print(f'consumer {consumer["name"]} has pending metrics past acceptable execution time')
                    message_ids = [i["message_id"] for i in pending]
                    claimed = self.r.xclaim(self.keys.stream_key, self.keys.group_key, consumer["name"],
                                            since_delivered,
                                            message_ids)
                    to_do += claimed
        if to_do and self.send_to_datadog([encoded_dict for timestamp, encoded_dict in to_do]):
            ts = [timestamp for timestamp, encoded_dict in to_do]
            return self.xack(ts)
