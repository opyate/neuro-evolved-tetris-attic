from typing import List, Dict, Tuple, Optional
import random


class TetrisEngine:
    def __init__(self, width: int = 10, height: int = 20) -> None:
        self.width: int = width
        self.height: int = height
        self.grid: List[List[int]] = [
            [0 for _ in range(self.width)] for _ in range(self.height)
        ]
        self.current_piece: Optional[Dict[str, int]] = None
        self.next_piece: Optional[Dict[str, int]] = None
        self.bag: List[str] = []  # For "bag of seven" piece generation
        self.score_for_current_tick: int = 0
        self.total_score: int = 0
        self.is_game_over: bool = False
        self.moves_made: List[str] = []
        self.count_ticks: int = 0
        self.wall_kick_cache: Dict[str, bool] = {}  # to prevent hovering pieces
        self.shapes: Dict[str, List[List[List[int]]]] = self.get_shapes()
        self.scores: List[int] = [0, 100, 300, 500, 800]
        self.generate_new_piece()  # Start with a piece
        self.update_grid()

    def to_dict(self) -> Dict:
        return {
            "score": self.total_score,
            "isGameOver": self.is_game_over,
            "grid": self.grid,
        }

    def get_shapes(self) -> Dict[str, List[List[List[int]]]]:
        return {
            "I": [
                [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
                [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0]],
                [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0]],
                [[0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0]],
            ],
            "J": [
                [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
                [[0, 1, 1], [0, 1, 0], [0, 1, 0]],
                [[0, 0, 0], [1, 1, 1], [0, 0, 1]],
                [[0, 1, 0], [0, 1, 0], [1, 1, 0]],
            ],
            "L": [
                [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
                [[0, 1, 0], [0, 1, 0], [0, 1, 1]],
                [[0, 0, 0], [1, 1, 1], [1, 0, 0]],
                [[1, 1, 0], [0, 1, 0], [0, 1, 0]],
            ],
            "O": [
                [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
                [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
                [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
                [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
            ],
            "S": [
                [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
                [[0, 1, 0], [0, 1, 1], [0, 0, 1]],
                [[0, 0, 0], [0, 1, 1], [1, 1, 0]],
                [[1, 0, 0], [1, 1, 0], [0, 1, 0]],
            ],
            "T": [
                [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
                [[0, 1, 0], [0, 1, 1], [0, 1, 0]],
                [[0, 0, 0], [1, 1, 1], [0, 1, 0]],
                [[0, 1, 0], [1, 1, 0], [0, 1, 0]],
            ],
            "Z": [
                [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
                [[0, 0, 1], [0, 1, 1], [0, 1, 0]],
                [[0, 0, 0], [1, 1, 0], [0, 1, 1]],
                [[0, 1, 0], [1, 1, 0], [1, 0, 0]],
            ],
        }

    def get_piece_from_bag(self) -> Dict[str, int]:
        if not self.bag:
            self.bag = list(self.shapes.keys())
            self.shuffle_bag()

        shape_type: str = self.bag.pop()
        piece_shape: List[List[int]] = self.get_piece_shape(shape_type, 0)
        top_row_offset: int = next(
            i for i, row in enumerate(piece_shape) if any(cell == 1 for cell in row)
        )

        leftmost_col: int = min(
            (col for row in piece_shape for col, cell in enumerate(row) if cell),
            default=0,
        )
        rightmost_col: int = max(
            (col for row in piece_shape for col, cell in enumerate(row) if cell),
            default=0,
        )
        center_col: int = (leftmost_col + rightmost_col) // 2

        piece: Dict[str, int] = {
            "type": shape_type,
            "rotation": 0,
            "x": self.width // 2 - center_col,
            "y": -top_row_offset,
        }

        return piece

    def generate_new_piece(self) -> None:
        self.current_piece = self.get_piece_from_bag()
        if not self.next_piece:
            self.generate_next_piece()

    def generate_next_piece(self) -> None:
        self.next_piece = self.get_piece_from_bag()
        self.wall_kick_cache = {}

    def shuffle_bag(self) -> None:
        random.shuffle(self.bag)

    def has_single_repetitions(self) -> bool:
        N: int = 20
        if len(self.moves_made) < N:
            return False

        last_move: str = self.moves_made[-1]
        if last_move in ["up", "down"]:
            return False

        last_N_moves: List[str] = self.moves_made[-N:]
        return all(move == last_N_moves[0] for move in last_N_moves)

    def has_double_repetitions(self) -> bool:
        N: int = 30
        if len(self.moves_made) < N:
            return False

        last_move: str = self.moves_made[-1]
        if last_move in ["up", "down"]:
            return False

        last_N_moves: List[str] = self.moves_made[-N:]
        first_moves: List[str] = last_N_moves[::2]
        second_moves: List[str] = last_N_moves[1::2]

        return all(move == first_moves[0] for move in first_moves) and all(
            move == second_moves[0] for move in second_moves
        )

    def has_repetitions(self) -> bool:
        return self.has_single_repetitions() or self.has_double_repetitions()

    def tick(self) -> None:
        if self.is_game_over or not self.current_piece:
            return
        self.count_ticks += 1
        self.score_for_current_tick = 0

        if self.is_valid_move(
            self.current_piece["x"],
            self.current_piece["y"] + 1,
            self.current_piece["rotation"],
        ):
            self.current_piece["y"] += 1
        else:
            self.lock_piece()
            self.clear_lines()
            self.current_piece = self.next_piece
            self.generate_next_piece()

            if not self.is_valid_move(
                self.current_piece["x"],
                self.current_piece["y"],
                self.current_piece["rotation"],
            ):
                self.is_game_over = True

        self.update_grid()

    def move_piece(self, move: str) -> None:
        if self.is_game_over or not self.current_piece:
            return
        self.moves_made.append(move)

        if self.has_repetitions():
            self.is_game_over = True
            self.update_grid()
            return

        if move == "up":
            while self.is_valid_move(
                self.current_piece["x"],
                self.current_piece["y"] + 1,
                self.current_piece["rotation"],
            ):
                self.current_piece["y"] += 1
            self.lock_piece()
            self.clear_lines()
            self.current_piece = self.next_piece
            self.generate_next_piece()
            if not self.is_valid_move(
                self.current_piece["x"],
                self.current_piece["y"],
                self.current_piece["rotation"],
            ):
                self.is_game_over = True
            self.update_grid()
        elif move == "down":
            if self.is_valid_move(
                self.current_piece["x"],
                self.current_piece["y"] + 1,
                self.current_piece["rotation"],
            ):
                self.current_piece["y"] += 1
                self.update_grid()
        elif move == "left":
            if self.is_valid_move(
                self.current_piece["x"] - 1,
                self.current_piece["y"],
                self.current_piece["rotation"],
            ):
                self.current_piece["x"] -= 1
                self.update_grid()
        elif move == "right":
            if self.is_valid_move(
                self.current_piece["x"] + 1,
                self.current_piece["y"],
                self.current_piece["rotation"],
            ):
                self.current_piece["x"] += 1
                self.update_grid()
        elif move == "rotate_cw":
            self.rotate_piece(1)
        elif move == "rotate_ccw":
            self.rotate_piece(-1)

    def is_valid_move(self, x: int, y: int, rotation: int) -> bool:
        piece: List[List[int]] = self.get_piece_shape(
            self.current_piece["type"], rotation
        )

        for row in range(len(piece)):
            for col in range(len(piece[row])):
                if piece[row][col]:
                    new_x: int = x + col
                    new_y: int = y + row

                    if (
                        new_x < 0
                        or new_x >= self.width
                        or new_y >= self.height
                        or (new_y >= 0 and self.grid[new_y][new_x] not in [0, 1])
                    ):
                        return False

        return True

    def lock_piece(self) -> None:
        piece: List[List[int]] = self.get_piece_shape(
            self.current_piece["type"], self.current_piece["rotation"]
        )

        for row in range(len(piece)):
            for col in range(len(piece[0])):
                if piece[row][col]:
                    x: int = self.current_piece["x"] + col
                    y: int = self.current_piece["y"] + row

                    if y >= 0:
                        self.grid[y][x] = self.current_piece["type"]

    def clear_lines(self) -> None:
        full_row_indices: List[int] = [
            row
            for row in range(self.height)
            if all(cell != 0 for cell in self.grid[row])
        ]

        if not full_row_indices:
            return

        for row_index in full_row_indices:
            self.grid.pop(row_index)
            self.grid.insert(0, [0] * self.width)

        self.score_for_current_tick = self.scores[len(full_row_indices)]
        self.total_score += self.score_for_current_tick

    def get_piece_shape(self, type: str, rotation: int) -> List[List[int]]:
        return self.shapes[type][rotation]

    def rotate_piece(self, direction: int) -> None:
        if self.is_game_over or not self.current_piece:
            return

        new_rotation: int = (self.current_piece["rotation"] + direction) % 4
        piece_type: str = self.current_piece["type"]

        if piece_type == "O":
            return

        wall_kick_data_for_jlszt: Dict[str, List[Tuple[int, int]]] = {
            "0->R": [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
            "R->0": [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
            "R->2": [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
            "2->R": [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
            "2->L": [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
            "L->2": [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
            "L->0": [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
            "0->L": [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
        }

        wall_kick_data: Dict[str, Dict[str, List[Tuple[int, int]]]] = {
            "O": {},
            "I": {
                "0->R": [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
                "R->0": [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
                "R->2": [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
                "2->R": [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
                "2->L": [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
                "L->2": [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
                "L->0": [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
                "0->L": [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
            },
            "J": wall_kick_data_for_jlszt,
            "L": wall_kick_data_for_jlszt,
            "S": wall_kick_data_for_jlszt,
            "T": wall_kick_data_for_jlszt,
            "Z": wall_kick_data_for_jlszt,
        }

        start_rotation_state: str = (
            "R"
            if self.current_piece["rotation"] == 1
            else (
                "L"
                if self.current_piece["rotation"] == 3
                else str(self.current_piece["rotation"])
            )
        )
        end_rotation_state: str = (
            "R"
            if new_rotation == 1
            else ("L" if new_rotation == 3 else str(new_rotation))
        )
        current_rotation_state: str = f"{start_rotation_state}->{end_rotation_state}"

        for test in wall_kick_data[piece_type][current_rotation_state]:
            new_x: int = self.current_piece["x"] + test[0]
            new_y: int = self.current_piece["y"] + test[1]

            cache_key: str = (
                f"{piece_type}-{self.current_piece['x']}-{self.current_piece['y']}-{current_rotation_state}-{test[0]}-{test[1]}"
            )
            if self.wall_kick_cache.get(cache_key):
                continue

            if self.is_valid_move(new_x, new_y, new_rotation):
                self.current_piece["x"] = new_x
                self.current_piece["y"] = new_y
                self.current_piece["rotation"] = new_rotation
                self.wall_kick_cache[cache_key] = True
                self.update_grid()
                return

    def update_grid(self) -> None:
        new_grid: List[List[int]] = [
            [0 for _ in range(self.width)] for _ in range(self.height)
        ]

        for row in range(self.height):
            for col in range(self.width):
                if isinstance(self.grid[row][col], str):
                    new_grid[row][col] = self.grid[row][col]

        if self.current_piece:
            piece_shape: List[List[int]] = self.get_piece_shape(
                self.current_piece["type"], self.current_piece["rotation"]
            )

            for row in range(len(piece_shape)):
                for col in range(len(piece_shape[0])):
                    if piece_shape[row][col]:
                        x: int = self.current_piece["x"] + col
                        y: int = self.current_piece["y"] + row
                        if 0 <= x < self.width and 0 <= y < self.height:
                            new_grid[y][x] = 1

        self.grid = new_grid
