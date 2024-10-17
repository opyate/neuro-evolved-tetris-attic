import time
from contextlib import asynccontextmanager

import redis
from app import driver
from app.db_without_pipelines import db_load_all_dicts, db_load_all_dicts_by_key
from app.tetris_bot import TetrisBot
from celery.result import AsyncResult
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

result = None
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
async def root():
    return FileResponse("static/index.html")


@app.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    dict_result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result,
    }
    return JSONResponse(dict_result)


@app.get("/start")
async def start(n: int = 10, f: str = ""):
    global result

    if result is None:

        bot_opts = {"width": 10, "height": 10}
        bots = [TetrisBot(bot_id, **bot_opts) for bot_id in range(n)]
        result = driver.main(bots)

        return {"message": f"Started {n} bots"}
    else:

        start_time = time.time()
        bots = db_load_all_dicts(r, range(n))
        result = driver.main(bots)
        end_time = time.time()
        print(f"New round prep {end_time - start_time:.2f} seconds")

        return {"message": f"Next round for {n} bots"}


@app.get("/ping")
async def ping():
    return {"message": "pong", "redis": r.ping()}


@app.get("/job")
async def job_state():
    global result
    if result is not None:
        result_get = "waiting..."
        is_all_game_over = False
        if result.successful():
            # global result
            result_get = result.get()
            is_all_game_over = all([result["all_game_over"] for result in result_get])

        return {
            "message": "Latest job state",
            "ready": result.ready(),
            "successful": result.successful(),
            "failed": result.failed(),
            # "waiting": result.waiting(),
            # "completed_count": result.completed_count(),
            "is_all_game_over": is_all_game_over,
            "result": result_get,
            "result_get_force": result.get(),
        }
    else:
        return {"message": "No job started"}


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
