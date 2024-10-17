import random
import time


class FakeEngine:
    def __init__(
        self,
    ):
        self.is_game_over = False

    def to_dict(self):
        return {"is_game_over": self.is_game_over}

    def __repr__(self) -> str:
        return f"FakeEngine(is_game_over={self.is_game_over})"

    @classmethod
    def from_dict(cls, data):
        engine = cls()
        engine.is_game_over = data["is_game_over"]
        return engine


class TetrisBot:
    def __init__(self, bot_id: int, **kwargs):
        self.id = bot_id
        self.engine = FakeEngine()
        self.state = {"acc": 0.0, "number_of_thinks": 0}

    def __repr__(self):
        return f"TetrisBot(id={self.id}, state={self.state}, engine={self.engine})"

    def think_then_move(self, do_tick: bool):
        if not self.engine.is_game_over:
            rnd = random.random()
            self.state.update(
                {
                    "acc": self.state["acc"] + rnd,
                    "number_of_thinks": self.state["number_of_thinks"] + 1,
                }
            )
            time.sleep(rnd / 100)
            self.engine.is_game_over = rnd < 0.01
            return True
        return False

    def get_state(self):
        return {"id": self.id, "state": self.state, "engine": self.engine.to_dict()}

    def to_dict(self, lite=True):
        return {"id": self.id, "state": self.state, "engine": self.engine.to_dict()}

    @classmethod
    def from_dict(cls, data):
        bot = cls(data["id"])
        bot.state = data["state"]
        bot.engine = FakeEngine.from_dict(data["engine"])
        bot.engine.is_game_over = data["engine"]["is_game_over"]
        return bot
