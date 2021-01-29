#! /bin/env python3
import os
import fire
from espnet import EspNetSystem

if __name__ == "__main__":
    if not os.environ.get('REDIS_URL'):
        os.environ['REDIS_URL'] = 'unix:///var/run/redis/redis-server.sock?db=0'
    fire.Fire(EspNetSystem())
