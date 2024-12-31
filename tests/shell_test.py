import asyncio

from fastapi.testclient import TestClient

from src.config import AppConfig
from src.scheduler import SchedulerApi
from src.shell import Shell, build_app
from src.worker import CompletionResponse


class StubScheduler(SchedulerApi):
    def __init__(self) -> None:
        self.requests: list[str] = []

    async def complete(self, prompt: str) -> CompletionResponse:
        self.requests.append(prompt)
        return CompletionResponse(completion=prompt, tokens=len(prompt))


async def test_shell_can_be_shutdown():
    # Given a running shell
    config = AppConfig.with_free_port()
    scheduler = StubScheduler()
    shell = Shell(config, scheduler)
    loop = asyncio.get_event_loop()
    task = loop.create_task(shell.run())

    # wait for the server to start
    await asyncio.sleep(0.01)

    # When the shell is shutdown
    shell.shutdown()

    # Then the shell task is done after 1 second
    await asyncio.wait_for(task, timeout=1.0)


def test_health():
    # given an app
    app = build_app(StubScheduler())
    client = TestClient(app)

    # when we call the health route
    response = client.get("/health")

    # then we get a 200 response
    assert response.status_code == 200
    assert response.json() == "ok"


def test_complete():
    # given an app with a scheduler
    scheduler = StubScheduler()
    app = build_app(scheduler)

    # when we call the jobs route
    with TestClient(app) as client:
        response = client.post("/complete", json={"prompt": "hello"})

    # then we get a 200 response
    assert response.status_code == 200
    assert response.json() == "hello"
