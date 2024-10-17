import asyncio
import cProfile
from contextlib import asynccontextmanager

from app.world import run_bots_continuous, stop_bots
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

latest_bot_states = {}
# Global task variable to keep track of the running simulation
current_simulation_task = None
use_profiler = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    if use_profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    yield
    await stop()

    if use_profiler:
        profiler.disable()  # Stop profiling
        profiler.dump_stats("profiling_results.prof")
        # profiler.print_stats(sort="cumtime")


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        # https://reqbin.com/req/doog8aai/http-headers-to-prevent-caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app = FastAPI(lifespan=lifespan)
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/start")
async def start(n: int = 10):
    print("/start")
    global current_simulation_task
    if current_simulation_task:
        return {"message": "Simulation already running"}

    bot_opts = {"width": 10, "height": 10}
    current_simulation_task = asyncio.create_task(
        run_bots_continuous(n, latest_bot_states, bot_opts=bot_opts)
    )
    return {"message": f"Started {n} bots"}


@app.get("/stop")
async def stop():
    print("/stop")
    await stop_bots()

    global current_simulation_task
    if current_simulation_task:
        current_simulation_task.cancel()  # Cancel the current simulation task
        current_simulation_task = None

    return {"message": "Stopped all bots"}


@app.get("/state")
async def state():
    return {"message": "Latest bot states", "latest_bot_states": latest_bot_states}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "tick":
                # print("tick")
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
