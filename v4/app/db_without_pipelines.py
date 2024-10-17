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
    success = True
    for bot in bots:
        success = success and db_save(r, bot, key)
    return success


def db_save_all_dict(r: redis.Redis, bots: list[dict], key: str = "bot"):
    success = True
    for bot in bots:
        bot_id = bot["id"]
        ser_bot = pickle.dumps(bot)
        success = success and r.set(f"{key}:{bot_id}", ser_bot)
    return success


def db_load_all(
    r: redis.Redis, bot_ids: list[int], key: str = "bot"
) -> list[TetrisBot]:
    bots = []
    for bot_id in bot_ids:
        bot_data = r.get(f"{key}:{bot_id}")
        if bot_data is not None:
            bot = TetrisBot.from_dict(pickle.loads(bot_data))
            bots.append(bot)
    return bots


def db_load_all_dicts(
    r: redis.Redis, bot_ids: list[int], key: str = "bot"
) -> list[dict]:
    bots = []
    for bot_id in bot_ids:
        bot_data = r.get(f"{key}:{bot_id}")
        if bot_data is not None:
            bot = pickle.loads(bot_data)
            bots.append(bot)
    return bots


def db_load_all_dicts_by_key(r: redis.Redis, key: str = "bot") -> list[dict]:
    keys = r.keys(f"{key}:*")
    bots = []
    for key in keys:
        bot_data = r.get(key)
        if bot_data is not None:
            bot = pickle.loads(bot_data)
            bots.append(bot)
    return bots
