import asyncio
from typing import AsyncGenerator

import pytest

from src.scheduler import Scheduler
from src.worker import CompletionResponse, WorkerApi


class SpyWorker(WorkerApi):
    def __init__(self) -> None:
        self.calls: int = 0

    async def complete(self, prompts: list[str]) -> list[CompletionResponse]:
        self.calls += 1
        return [
            CompletionResponse(completion=prompt, tokens=len(prompt))
            for prompt in prompts
        ]


@pytest.fixture
def worker() -> SpyWorker:
    return SpyWorker()


@pytest.fixture
async def scheduler(worker: SpyWorker) -> AsyncGenerator[Scheduler, None]:
    scheduler = Scheduler(worker, max_wait_time=0.1)
    loop = asyncio.get_event_loop()
    task = loop.create_task(scheduler.run())
    yield scheduler
    task.cancel()


async def test_scheduler_completes_prompts(scheduler: Scheduler, worker: SpyWorker):
    # When adding a prompt to a running scheduler
    completion = await scheduler.complete("prompt")

    # Then the prompt is completed
    assert completion.completion == "prompt"

    # And the worker is only called once
    assert worker.calls == 1


async def test_scheduler_completes_prompts_in_batches(
    scheduler: Scheduler, worker: SpyWorker
):
    # When adding 8 prompts to a running scheduler
    await asyncio.gather(*[scheduler.complete(f"prompt {i}") for i in range(8)])

    # Then the worker is only called once
    assert worker.calls == 1


async def test_scheduler_shutdown():
    # Given a scheduler with a worker that hangs forever
    class HangingWorker(WorkerApi):
        async def complete(self, prompts: list[str]) -> list[CompletionResponse]:
            # create an event that will never be set
            event = asyncio.Event()
            await event.wait()
            return [
                CompletionResponse(completion=prompt, tokens=len(prompt))
                for prompt in prompts
            ]

    worker = HangingWorker()
    scheduler = Scheduler(worker, max_wait_time=0.1)
    task = asyncio.create_task(scheduler.run())

    # When a completion is requested
    asyncio.create_task(scheduler.complete("prompt"))

    # Then the scheduler can still be shutdown
    scheduler.shutdown()
    await task
