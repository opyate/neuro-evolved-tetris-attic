import torch
import torch.nn as nn
import torch.optim as optim
from app.tetris_brain import TetrisBrain, crossover, mutate
from app.tetris_engine import TetrisEngine


class TetrisBot:
    """A self-playing Tetris game.

    It uses a neural network to play the game,
    by predicting the next move.

    Contains game state.

    Crossover sets a next_brain attribute, so that crossover
    doesn't affect other brains currently in use.
    This allows us to crossover all bots at once, then
    reinitialise them with their next_brain.
    """

    def __init__(
        self, bot_id: int, width: int = 10, height: int = 20, brain: TetrisBrain = None
    ):
        self.id = bot_id
        self.width = width
        self.height = height
        self.engine = TetrisEngine(width, height)
        self.fitness = 0
        self.next_brain = None
        if brain is not None:
            self.brain = brain
        else:
            self.brain = TetrisBrain(width, height)

    def reinit(self):
        self.brain = self.next_brain
        self.next_brain = None
        self.engine = TetrisEngine(self.width, self.height)
        self.fitness = 0

    def get_game_state_as_inputs(self) -> torch.Tensor:
        """Returns game state as inputs for the neural network.

        cellValue is one of the following:
        - 0: empty cell
        - 1: piece-in-play
        - I/T/S/Z/J/L/O: locked piece

        Let the locked pieces be 0.5
        If the cell value is not a number, set it to 0.5

        Returns:
            torch.Tensor: Inputs for the neural network
        """
        inputs = torch.zeros(self.height * self.width, dtype=torch.float32)
        index = 0
        for row in range(self.height):
            for col in range(self.width):
                cell_value = self.engine.grid[row][col]
                inputs[index] = (
                    float(cell_value) if isinstance(cell_value, int) else 0.5
                )
                index += 1
        return inputs

    def think_then_move(self, do_tick: bool = False) -> bool:
        if self.engine.is_game_over:
            return False

        inputs = self.get_game_state_as_inputs().unsqueeze(0)  # Add batch dimension

        this = self
        with torch.no_grad():
            results = this.brain(inputs)

        # Get the move with the highest probability
        move_index = torch.argmax(results).item()
        move = ["left", "right", "up", "down", "rotate_cw", "rotate_ccw", "noop"][
            move_index
        ]

        # print(f"Bot {self.id} move: {move}, tick: {do_tick}")

        self.engine.move_piece(move)

        # Incentivise movement
        if move != "noop":
            self.fitness += 1

        if do_tick:
            # Incentivise longevity
            self.fitness += 1
            self.engine.tick()
            self.fitness += self.engine.score_for_current_tick

        return True

    def crossover(self, parent_a: "TetrisBot", parent_b: "TetrisBot") -> None:
        child_brain = crossover(parent_a.brain, parent_b.brain)
        mutate(child_brain, mutation_rate=0.01)
        self.next_brain = child_brain

    def __repr__(self):
        return f"TetrisBot(id={self.id}, w={self.width}, h={self.height}, fitness={self.fitness}, engine={self.engine})"

    def to_dict(self, with_weights=False) -> dict:
        as_dict = {
            "id": self.id,
            "width": self.width,
            "height": self.height,
            "engine": self.engine.to_dict(),
            "fitness": self.fitness,
        }

        if with_weights:
            as_dict["brain"] = self.brain.to_dict()
            as_dict["next_brain"] = (
                self.next_brain.to_dict() if self.next_brain else None
            )

        return as_dict

    @classmethod
    def from_dict(cls, data):
        bot = cls(
            data["id"],
            data["width"],
            data["height"],
            TetrisBrain.from_dict(data["width"], data["height"], data["brain"]),
        )
        bot.fitness = data["fitness"]
        if data["next_brain"]:
            bot.next_brain = TetrisBrain.from_dict(
                data["width"], data["height"], data["next_brain"]
            )
        bot.engine = TetrisEngine.from_dict(data["engine"])
        return bot
