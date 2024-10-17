import asyncio
import functools

import redis
from app.fake_bot import TetrisBot

r = redis.Redis(host="redis", port=6379, db=0)


@functools.lru_cache(maxsize=1)
def get_worker_index():
    index = r.incr(f"worker_index")
    return index - 1


class Coordinator:
    def __init__(self, number_of_workers: int):
        self.id = get_worker_index()
        self.number_of_workers = number_of_workers

    async def wait_for_all_workers(self, tick: int):
        tick_key = f"tick:{tick}"

        # Set the tick for the current worker in a Redis hash
        r.hset(tick_key, self.id, tick)

        # Wait until the hash length is equal to the number of workers
        while r.hlen(tick_key) < self.number_of_workers:
            await asyncio.sleep(0.1)
