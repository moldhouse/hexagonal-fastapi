from contextlib import asynccontextmanager
from typing import AsyncIterator, TypedDict, cast

from fastapi import APIRouter, Depends, FastAPI, Request
from pydantic import BaseModel
from uvicorn import Config, Server

from src.config import AppConfig
from src.scheduler import SchedulerApi


def health() -> str:
    return "ok"


def scheduler(request: Request) -> SchedulerApi:
    return cast(SchedulerApi, request.state.scheduler)


class CompletionBody(BaseModel):
    prompt: str


async def complete(
    body: CompletionBody, scheduler: SchedulerApi = Depends(scheduler)
) -> str:
    response = await scheduler.complete(body.prompt)
    return response.completion


def routes() -> APIRouter:
    router = APIRouter()
    router.add_api_route("/health", health)
    router.add_api_route("/complete", complete, methods=["POST"])
    return router


class ShellState(TypedDict):
    """State that is shared between requests."""

    scheduler: SchedulerApi


def build_app(scheduler: SchedulerApi) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[ShellState]:
        yield {"scheduler": scheduler}

    app = FastAPI(lifespan=lifespan)
    app.include_router(routes())
    return app


class Shell:
    """Provide user access to our application."""

    def __init__(self, config: AppConfig, scheduler: SchedulerApi) -> None:
        self.config = config
        self.app = build_app(scheduler)
        self.server: Server | None = None

    async def run(self) -> None:
        config = Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            loop="asyncio",
            lifespan="on",
        )
        self.server = Server(config)
        await self.server.serve()

    def shutdown(self) -> None:
        """Gracefully shut down the server"""
        if self.server is None:
            raise RuntimeError("Server not running")
        self.server.should_exit = True
