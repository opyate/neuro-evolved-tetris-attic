import multiprocessing

from app.tetris_bot import TetrisBot
from app.worker import bots_next_round, bots_think_then_move
from celery import chord
from celery.result import AsyncResult

num_cores = multiprocessing.cpu_count() - 2


def chunkify(lst, n):
    """Splits list into n chunks."""
    return [lst[i::n] for i in range(n)]


def main(bots: list[TetrisBot] | list[dict]) -> AsyncResult:
    """Hand bots off to Celery workers.

    If this is first round, bots should be a list of TetrisBot objects, as
    they would have been initialised in the server.
    If this is the second+ round, bots should be a list of dicts, as they
    would have been read from Redis.
    """

    # Check if the list contains TetrisBot objects
    # if all(isinstance(bot, TetrisBot) for bot in bots):
    if isinstance(bots[0], TetrisBot):
        bots = [bot.to_dict(lite=False) for bot in bots]

    # print(f">>> bot type: {type(bots[0])}, bot: {bots[0]}")

    return chord(
        (
            bots_think_then_move.s(bots_slice)
            for bots_slice in chunkify(bots, num_cores)
            if len(bots_slice) > 0
        )
    )(bots_next_round.s())
