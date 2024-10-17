import pickle

import redis
from app.tetris_bot import TetrisBot

# maybe? https://redis.io/docs/latest/develop/connect/clients/python/redis-py/#example-indexing-and-querying-json-documents


def db_save(r: redis.Redis, bot: TetrisBot, key: str = "bot"):
    bot_id = bot.id
    bot_dict = bot.to_dict()
    ser_bot = pickle.dumps(bot_dict)
    return r.set(f"{key}:{bot_id}", ser_bot)


def db_load(r: redis.Redis, bot_id: int, key: str = "bot") -> TetrisBot:
    deser_bot = TetrisBot.from_dict(pickle.loads(r.get(f"{key}:{bot_id}")))
    return deser_bot


def db_save_all(r: redis.Redis, bots: list[TetrisBot], key: str = "bot"):
    with r.pipeline() as pipe:
        pipe.multi()
        for bot in bots:
            db_save(pipe, bot, key)
        return all(pipe.execute())


def db_save_all_dict(r: redis.Redis, bots: list[dict], key: str = "bot"):
    with r.pipeline() as pipe:
        pipe.multi()
        for bot in bots:
            bot_id = bot["id"]
            ser_bot = pickle.dumps(bot)
            pipe.set(f"{key}:{bot_id}", ser_bot)
        return all(pipe.execute())


def db_load_all(
    r: redis.Redis, bot_ids: list[int], key: str = "bot"
) -> list[TetrisBot]:
    with r.pipeline() as pipe:
        pipe.multi()
        for bot_id in bot_ids:
            pipe.get(f"{key}:{bot_id}")
        serialized_bots = pipe.execute()
    bots = [
        TetrisBot.from_dict(pickle.loads(bot_data))
        for bot_data in serialized_bots
        if bot_data is not None
    ]
    return bots


def db_load_all_dicts(
    r: redis.Redis, bot_ids: list[int], key: str = "bot"
) -> list[dict]:
    with r.pipeline() as pipe:
        pipe.multi()
        for bot_id in bot_ids:
            pipe.get(f"{key}:{bot_id}")
        serialized_bots = pipe.execute()
    bots = [
        pickle.loads(bot_data) for bot_data in serialized_bots if bot_data is not None
    ]
    return bots


def db_load_all_dicts_by_key(r: redis.Redis, key: str = "bot") -> list[dict]:
    keys = r.keys(f"{key}:*")
    with r.pipeline() as pipe:
        pipe.multi()
        for key in keys:
            pipe.get(key)
        serialized_bots = pipe.execute()
    bots = [
        pickle.loads(bot_data) for bot_data in serialized_bots if bot_data is not None
    ]
    return bots


def db_write_bots_fitness(r: redis.Redis, bots: list[TetrisBot]):
    # Write the bots' id and fitness pairs to a Redis list
    for bot in bots:
        r.rpush("bot_fitness", f"{bot.id}:{bot.fitness}")


def db_read_bots_fitness(r: redis.Redis, expected_size: int) -> list:
    # Initialize a list of the expected size with None or some default value
    fitness_list = [None] * expected_size

    # bot IDs
    bot_ids = set()

    # Retrieve all entries from the Redis list
    bot_fitness_list = r.lrange("bot_fitness", 0, -1)

    # Parse the list and populate the fitness values at the correct index
    for entry in bot_fitness_list:
        bot_id, fitness = entry.decode("utf-8").split(":")
        bot_id = int(bot_id)  # Convert bot_id to integer to use as an index
        fitness_list[bot_id] = float(fitness)  # Place fitness in the correct index
        bot_ids.add(bot_id)

    # assert that the number of bot_ids equals expected_size
    assert len(bot_ids) == expected_size, "not enough fitness values"

    return fitness_list
