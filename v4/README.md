# Intro

v4 of Tetris neuro-evolved NNs which uses Celery workers.

# Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip3 install torch --index-url https://download.pytorch.org/whl/cu124
echo PYTHONPATH=$(pwd) > .env
```

Got redis.conf from:

```
curl -O https://raw.githubusercontent.com/redis/redis/refs/tags/7.4.0/redis.conf 
```

# Run

```
docker compose up
```

Then visit

http://127.0.0.1:8000/

# Debug

See the debug string for the first bot:

```
curl http://127.0.0.1:8000/state | jq '.latest_bot_states.bots[0].debug'
```

# Task definition

I am building a neuro-evolutionary simulation of bots learning to play Tetris using Python and PyTorch, which does the following:

- spawn thousands of bots from the simulation runner, and have a bots_list of size N
- the bots are initialised with a zeroed PyTorch network, which has 10x20 inputs, and 7 outputs
- each bot has a state, in the form of a Tetris engine
- the PyTorch network's inputs represent the Tetris grid, and the 7 outputs represent the 7 moves a bot can make: up, down, left, right, rotate_clockwise, rotate_counter_clockwise, or noop (which means "make no move", or "no operation")
- the simulation loop now starts, and the runner asks each bot to predict their next move
- after each bot made their move, they get one fitness point for staying alive, and many more fitness points for scoring (i.e. clearing lines on the Tetris grid)
- after each bot made their move, they might also be in a game over state
- after all bots reach game over, the evolution starts
- evolution step 1: parents are chosen based on a weighted selection
- evolution step 2: the parents are crossed-over, to produce a child
- evolution step 3: the child is slightly mutated
- set each bot's next_brain to the new child
- the entire bots_list is re-initialised so their next_brain becomes their current_brain
- the simulation loops
