import os
import time
from contextlib import asynccontextmanager

import redis
from app.db_without_pipelines import db_load_all_dicts, db_load_all_dicts_by_key
from app.tetris_bot import TetrisBot
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

load_dotenv()
NUMBER_OF_WORKERS = int(os.getenv("NUMBER_OF_WORKERS", 1))
BOTS_PER_WORKER = int(os.getenv("BOTS_PER_WORKER", 1))
r: redis.Redis = None


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        # https://reqbin.com/req/doog8aai/http-headers-to-prevent-caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    global r
    r = redis.Redis(host="redis", port=6379, db=0)

    # smoke test redis:
    # bot_ids = bots = [bot_id for bot_id in range(3)]
    # bots = [TetrisBot(bot_id) for bot_id in bot_ids]
    # print(bots)
    # print("save:")
    # print(db_save_all(r, bots))
    # print("load:")
    # print(db_load_all(r, bot_ids))

    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/")
async def root(request: Request):

    if "n" not in request.query_params:
        n = NUMBER_OF_WORKERS * BOTS_PER_WORKER
        return RedirectResponse(url=f"/?n={n}")

    return FileResponse("static/index.html")


@app.get("/start")
async def start(n: int = 10, f: str = ""):
    # doesn't do anything anymore
    return {"message": f"Started {n} bots"}


@app.get("/ping")
async def ping():
    return {"message": "pong", "redis": r.ping()}


@app.get("/state")
async def state():

    latest_bot_states = db_load_all_dicts_by_key(r, "render_bot")

    return {"message": "Latest bot states", "latest_bot_states": latest_bot_states}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "tick":
                latest_bot_states = db_load_all_dicts_by_key(r, "render_bot")
                await manager.send(latest_bot_states, websocket)
            else:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)


manager = ConnectionManager()
