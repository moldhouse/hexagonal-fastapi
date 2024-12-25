from fastapi import APIRouter, FastAPI
from uvicorn import Config, Server


def read_root() -> str:
    return "Hello World"


def build_routes() -> APIRouter:
    router = APIRouter()
    router.add_api_route("/", read_root)
    return router


class Shell:
    """A representation of our shell"""

    def __init__(self) -> None:
        self.app = FastAPI()
        self.app.include_router(build_routes())

    async def run(self) -> None:
        config = Config(
            app=self.app, host="127.0.0.1", port=8000, loop="asyncio", lifespan="on"
        )
        server = Server(config)
        await server.serve()
