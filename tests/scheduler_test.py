import asyncio
from dataclasses import dataclass
from typing import AsyncGenerator

import pytest

from src.scheduler import Scheduler


@dataclass
class Spy:
    counter: int = 0


async def sleep_forever(spy: Spy | None = None):
    try:
        event = asyncio.Event()
        await event.wait()
    except asyncio.CancelledError:
        if spy:
            spy.counter += 1


@pytest.fixture
async def scheduler() -> AsyncGenerator[Scheduler, None]:
    scheduler = Scheduler()
    loop = asyncio.get_event_loop()
    task = loop.create_task(scheduler.run())
    yield scheduler
    task.cancel()
    await asyncio.sleep(0.001)


async def test_scheduler_polls_tasks(scheduler: Scheduler):
    # Given a running scheduler
    async def increments(spy: Spy):
        spy.counter += 1

    spy = Spy()

    # With a task that sleeps forever
    await scheduler.add_job("sleep_forever", sleep_forever())

    # When a task is added which increments a counter
    await scheduler.add_job("increments", increments(spy))

    # Then the counter is incremented after 1 ms
    await asyncio.sleep(0.001)
    assert spy.counter == 1

    # And the task is removed again from the scheduler
    assert scheduler.n_jobs() == 1


async def test_long_running_task_can_be_removed(scheduler: Scheduler):
    # Given a scheduler with a task running forever
    spy = Spy()
    await scheduler.add_job("sleep_forever", sleep_forever(spy))

    # When the task is removed
    await scheduler.cancel_job("sleep_forever")

    # Then the task is cancelled
    await asyncio.sleep(0.001)
    assert spy.counter == 1

    # And the task is removed from the scheduler
    assert not scheduler.n_jobs()


async def test_scheduler_shuts_down_tasks():
    # Given a scheduler with a task running forever which increments a counter on shutdown
    spy = Spy()
    scheduler = Scheduler()
    loop = asyncio.get_event_loop()
    task = loop.create_task(scheduler.run())
    await scheduler.add_job("sleep_forever", sleep_forever(spy))

    # Wait for 1 ms
    await asyncio.sleep(0.001)
    assert spy.counter == 0

    # Wait for the scheduler to shutdown
    task.cancel()
    await asyncio.sleep(0.001)

    # Then the all running tasks are cancelled and the counter is incremented
    assert spy.counter == 1
