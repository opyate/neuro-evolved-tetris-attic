import asyncio
import logging
import os
import socket
import traceback
from enum import Enum

import redis
from app.coordinator import Coordinator
from app.db import (
    db_load_all,
    db_read_bots_fitness,
    db_save_all_dict,
    db_write_bots_fitness,
)
from app.tetris_bot import TetrisBot
from app.tetris_engine import TetrisEngine
from app.worker_util import weighted_selection
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
UNIQ = socket.gethostname()
NUMBER_OF_WORKERS = int(os.getenv("NUMBER_OF_WORKERS", 1))
BOTS_PER_WORKER = int(os.getenv("BOTS_PER_WORKER", 1))
r = redis.Redis(host="redis", port=6379, db=0)


class EventType(Enum):
    TICK = "tick"
    MEGATICK = "megatick"


events = [EventType.TICK] * 8 + [EventType.MEGATICK] * 1


def crossover_with_fittest(bots: list[TetrisBot]):

    # read fitness values for all bots (for all workers) from redis
    # log(f"worker bots fitness: {[bot.fitness for bot in bots]}")
    all_fitness: list[float] = db_read_bots_fitness(
        r, NUMBER_OF_WORKERS * BOTS_PER_WORKER
    )
    max_fitness = max(all_fitness)
    min_fitness = min(all_fitness)
    mean_fitness = sum(all_fitness) / len(all_fitness)
    log(
        f"max_fitness: {max_fitness}, min_fitness: {min_fitness}, mean_fitness: {mean_fitness}"
    )

    total_fitness = sum(all_fitness)

    # Get the bot IDs for the bots who will spawn the next generation.
    potential_parent_ids_from_this_worker: set[int] = {bot.id for bot in bots}
    parent_ids_from_other_workers: set[int] = set()
    parent_pairs: list[tuple[int]] = []

    for _i in range(len(bots)):
        parent_a_id = weighted_selection(all_fitness, total_fitness)
        parent_b_id = weighted_selection(all_fitness, total_fitness)
        parent_pairs.append((parent_a_id, parent_b_id))

        # if a parent is not in parent_bots (i.e. it's from another worker), add it to parent_ids_from_other_workers
        if parent_a_id not in potential_parent_ids_from_this_worker:
            parent_ids_from_other_workers.add(parent_a_id)
        if parent_b_id not in potential_parent_ids_from_this_worker:
            parent_ids_from_other_workers.add(parent_b_id)

    # read other workers' bots from redis
    # log(f"crossover bots from other workers: {parent_ids_from_other_workers}")
    parent_bots_from_other_workers: list[TetrisBot] = db_load_all(
        r, list(parent_ids_from_other_workers)
    )
    parent_pool: list[TetrisBot] = bots + parent_bots_from_other_workers
    parent_pool_as_dict: dict[int, TetrisBot] = {bot.id: bot for bot in parent_pool}

    # log(f"parent_pool_as_dict: {parent_pool_as_dict.keys()}")

    for idx in range(len(bots)):
        bot = bots[idx]
        parent_a_id, parent_b_id = parent_pairs[idx]
        # log(f"bot {bot.id} parent_a_id={parent_a_id}, parent_b_id={parent_b_id}")
        parent_a = parent_pool_as_dict[parent_a_id]
        parent_b = parent_pool_as_dict[parent_b_id]

        # Crossover the two parents to produce a new child brain.
        # Even if parent_a and parent_b is the same brain, it will be slightly mutated
        bot.crossover(parent_a, parent_b)

    for bot in bots:
        bot.reinit()

    # no need to save the bots here, as the new PyTorch weights will be local to the worker
    # and not needed in another worker.


def bots_think_then_move(bots: list[TetrisBot]):

    # even though TetrisEngine has to_dict/from_dict, it's only used for rendering, and
    # we know we'll always need a fresh engine at this point
    for bot in bots:
        bot.engine = TetrisEngine(bot.width, bot.height)

    loop_count = 0
    while True:
        loop_count += 1

        event_count = 0
        for event in events:
            event_count += 1

            process_event(bots, event)

            # check if all bots are game over
            all_game_over = all(bot.engine.is_game_over for bot in bots)

            if all_game_over:
                db_result = db_save_all_dict(
                    r, [bot.to_dict(with_weights=False) for bot in bots], "render_bot"
                )
                if not db_result:
                    raise Exception("Failed to save render_bots to Redis")
                # use default key for bots with weights
                db_result = db_save_all_dict(
                    r, [bot.to_dict(with_weights=True) for bot in bots]
                )
                if not db_result:
                    raise Exception("Failed to save bots to Redis")

                # write bot ids and fitness values to redis
                db_write_bots_fitness(r, bots)

                log(f"loop_count={loop_count}, event_count={event_count}")
                return
            else:

                # We save bot state to Redis after every event, because the frontend will
                # try and render the bot states 60 times a second, by reading
                # from Redis via the "tick" websocket event.
                # We could potentially optimise here by writing to Redis less frequently.
                # E.g. whenever loop_count % N == 0 (every N loops)
                db_result = db_save_all_dict(
                    r, [bot.to_dict() for bot in bots], "render_bot"
                )
                if not db_result:
                    raise Exception("Failed to save render_bots to Redis")


def process_event(bots: list[TetrisBot], event: EventType):
    """For each bot, think and move based on the event.

    Returns nothing, as the bots are mutated in place.
    """
    do_tick = event == EventType.MEGATICK

    for bot in bots:
        # if bot.id == 0:
        #     logging.info(f">bot_before: {bot}")
        bot.think_then_move(do_tick)
        # if bot.id == 0:
        #     logging.info(f">bot_after: {bot}")


def log(msg: str):
    # print(msg, flush=True)
    logging.info(msg)


async def main():
    c = Coordinator(NUMBER_OF_WORKERS)

    logging.basicConfig(
        filename=f"/usr/src/app/logs/worker-{c.id}.log", level=logging.INFO
    )

    bot_opts = {"width": 10, "height": 10}
    bots = [
        TetrisBot(bot_id + (c.id * BOTS_PER_WORKER), **bot_opts)
        for bot_id in range(BOTS_PER_WORKER)
    ]
    # log(f"worker bots={[bot.id for bot in bots]}")

    tick = 1
    while True:
        await c.wait_for_all_workers(tick := tick + 1)
        bots_think_then_move(bots)
        await c.wait_for_all_workers(tick := tick + 1)
        crossover_with_fittest(bots)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        log(f"exception={e}")
        log(traceback.format_exc())
        raise e
