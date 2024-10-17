import asyncio
import concurrent.futures
import os
import random
import sys
import time
import traceback
from enum import Enum
from itertools import chain
from typing import Dict, List

from app.tetris_bot import TetrisBot

cpu_count = os.cpu_count()
max_workers = cpu_count - 1
print(f"max_workers: {max_workers}", flush=True)
log_file = "log.txt"
log_header = "loop_count,scorer_count,fitness_mean,fitness_min,fitness_max"
stop_event = asyncio.Event()


class EventType(Enum):
    TICK = "tick"
    MEGATICK = "megatick"


# Function to handle a chunk of bots' events
def handle_bots_event(
    bots: List[TetrisBot], event: EventType
) -> List[tuple[Dict, bool]]:
    do_tick = event == EventType.MEGATICK
    results = []

    for bot in bots:
        moved = bot.think_then_move(do_tick)
        _bot_state = bot.get_state(debug=False)
        bot_state = {
            **_bot_state,
            "engine": _bot_state["engine"].to_dict(),
        }
        results.append((bot_state, moved))

    return results


def crossover_with_fittest(bot, bots, total_fitness):
    parent_a_index = weighted_selection(bots, total_fitness)
    parent_b_index = weighted_selection(bots, total_fitness)

    parent_a = bots[parent_a_index]
    parent_b = bots[parent_b_index]

    # Crossover the two parents to produce a new child brain
    bot.crossover(parent_a, parent_b)
    return parent_a_index, parent_b_index


def chunkify(lst, n):
    """Splits list into n chunks."""
    return [lst[i::n] for i in range(n)]


def process_event(
    bot_chunks: List[List[TetrisBot]],
    event: EventType,
    state_queue: asyncio.Queue,
    executor: concurrent.futures.Executor,
):
    updated_bot_states = []

    # Dispatch the event to each chunk of bots concurrently
    futures = [executor.submit(handle_bots_event, chunk, event) for chunk in bot_chunks]

    # Gather all results and aggregate
    for future in concurrent.futures.as_completed(futures):
        try:
            bot_results = future.result()
            updated_bot_states.extend([bot_state for bot_state, _ in bot_results])
        except Exception as e:
            print(f"Exception: {e}", flush=True)
            print(traceback.format_exc(), flush=True)
            sys.exit(1)

    # Put the updated states in the queue for the main loop to consume
    asyncio.run_coroutine_threadsafe(
        state_queue.put(updated_bot_states), asyncio.get_running_loop()
    )


def when_all_game_over(
    bots: List[TetrisBot],
    executor: concurrent.futures.Executor,
    loop_count: int = 0,
):
    total_fitness = sum(bot.fitness for bot in bots)
    mean_fitness = total_fitness / len(bots)
    min_fitness = min(bot.fitness for bot in bots)
    max_fitness = max(bot.fitness for bot in bots)
    # number of bots with score > 0
    scorer_count = sum(1 for bot in bots if bot.engine.total_score > 0)

    log = f"{loop_count},{scorer_count},{mean_fitness:.2f},{min_fitness:.2f},{max_fitness:.2f}"
    print(
        log,
        flush=True,
    )
    with open(log_file, "a") as file:
        file.write(log + "\n")

    futures = [
        executor.submit(crossover_with_fittest, bot, bots, total_fitness)
        for bot in bots
    ]

    try:
        concurrent.futures.wait(futures)
    except Exception as e:
        print(f"Crossover Exception: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        sys.exit(1)

    for bot in bots:
        bot.reinit()


def weighted_selection(bots, total_fitness):
    index = 0
    start = random.uniform(0, 1)  # Random start point between 0 and 1

    while start > 0:
        normalised_fitness = bots[index].fitness / total_fitness
        start -= normalised_fitness
        index += 1

    index -= 1  # Adjust index because we incremented it at the end of the loop

    return index


async def run_bots_continuous(n: int, latest_states: Dict, bot_opts: dict = None):
    stop_event.clear()

    if bot_opts is None:
        bot_opts = {}

    bots = [TetrisBot(i, **bot_opts) for i in range(n)]
    global max_workers
    if len(bots) < max_workers:
        max_workers = len(bots)
    # Split the bots into chunks
    bot_chunks = chunkify(bots, max_workers)
    for i, chunk in enumerate(bot_chunks):
        print(f"Chunk {i}: {len(chunk)} bots", flush=True)

    # Create a queue to safely update latest_states
    state_queue = asyncio.Queue()

    loop_count = 0
    # 8 "tick" events followed by 1 "megatick"
    events = list(chain.from_iterable([[EventType.TICK] * 8, [EventType.MEGATICK] * 1]))

    # clear log file
    with open(log_file, "w") as file:
        print("Clearing log file", flush=True)
        file.write(log_header + "\n")

    # Create the thread pool once
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        print("Simulation started", flush=True)
        while not stop_event.is_set():
            loop_count += 1

            event_count = 0
            for event in events:
                event_count += 1

                start = time.time()
                process_event(bot_chunks, event, state_queue, executor)
                end_process_event = time.time()

                # Get updated states from the queue and update latest_states
                updated_bot_states = await state_queue.get()
                end_get_updated_states = time.time()

                # print(
                #     f"Process Event: {end_process_event - start:.5f}, Get Updated States: {end_get_updated_states - end_process_event:.5f}",
                #     flush=True,
                # )
                latest_states["bots"] = updated_bot_states
                latest_states["event_count"] = event_count
                latest_states["loop_count"] = loop_count

                # check if all bots are game over
                all_game_over = all(bot.engine.is_game_over for bot in bots)

                if all_game_over:
                    when_all_game_over(bots, executor, loop_count)
                    break

            # Control the simulation speed (for example, 60 ticks per second)
            # await asyncio.sleep(1 / 60)
        print("Simulation stopped", flush=True)


async def stop_bots():
    stop_event.set()
