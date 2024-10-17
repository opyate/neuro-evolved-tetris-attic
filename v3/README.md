# Intro

TL;RD ThreadPoolExecutor doesn't work well, because our task isn't IO-bound, but CPU-bound. TPE still does one thing at a time and has the GIL internally. See experiment 4, where we try Celery workers, so we can give tasks their own process (and own GIL).

v3 of Tetris neuro-evolved NNs which uses a client/server model.

Server: will host the thousands of brains, and use multi-processing for crossover and mutation, and keep brains in memory (less IO).
Client: similar to v1/v2 p5/canvas HTML to render simulations, but getting board states through web socket.

As the Tetris engine is not tied to game loops or rendering logic, potentially warm up the bots first with thousands/millions of iterations and check for scoring before we start rendering anything.

# Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip3 install torch --index-url https://download.pytorch.org/whl/cu124
echo PYTHONPATH=$(pwd) > .env
```

# Run

```
fastapi dev app/server.py
```

Then visit

http://127.0.0.1:8000/

# Debug

See the debug string for the first bot:

```
curl http://127.0.0.1:8000/state | jq '.latest_bot_states.bots[0].debug'
```
