from app.tetris_engine import TetrisEngine


engine = TetrisEngine(10, 10)
engine.grid
engine.current_piece

engine.move_piece("right")
