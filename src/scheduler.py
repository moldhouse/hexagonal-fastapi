import asyncio
import functools
from typing import Coroutine, NamedTuple

from src.shell import Shell


class AddJob(NamedTuple):
    name: str
    coroutine: Coroutine[None, None, None]


class CancelJob(NamedTuple):
    name: str


SchedulerMessage = AddJob | CancelJob


# alias for a function that returns on the first completed task
select = functools.partial(asyncio.wait, return_when=asyncio.FIRST_COMPLETED)


class Scheduler:
    """Keep track of a list of running tasks."""

    def __init__(self) -> None:
        self.jobs: list[asyncio.Task[None]] = []
        self.messages: asyncio.Queue[SchedulerMessage] = asyncio.Queue(0)

    async def add_job(self, name: str, coroutine: Coroutine[None, None, None]) -> None:
        await self.messages.put(AddJob(name, coroutine))

    async def cancel_job(self, name: str) -> None:
        await self.messages.put(CancelJob(name))

    def n_jobs(self) -> int:
        return len(self.jobs)

    async def run(self) -> None:
        try:
            local_tasks = []
            while True:
                if not self.jobs:
                    await self._wait_for_messages()
                else:
                    t1 = asyncio.create_task(self._wait_for_messages())
                    t2 = asyncio.create_task(self._wait_for_tasks())
                    local_tasks = [t1, t2]
                    _, pending = await select(local_tasks)
                    pending.pop().cancel()
        except asyncio.CancelledError:
            for task in local_tasks:
                task.cancel()
            await self._shutdown()

    async def _wait_for_tasks(self) -> None:
        done, _ = await select(self.jobs)
        for task in done:
            self.jobs.remove(task)

    async def _wait_for_messages(self) -> None:
        message = await self.messages.get()
        await self._handle_message(message)

    async def _handle_message(self, message: SchedulerMessage) -> None:
        match message:
            case AddJob(name, coroutine):
                self.jobs.append(asyncio.create_task(coroutine, name=name))
            case CancelJob(name):
                for task in self.jobs:
                    if task.get_name() == name:
                        task.cancel()
                        self.jobs.remove(task)
                        break

    async def _shutdown(self) -> None:
        for task in self.jobs:
            task.cancel()


class App:
    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            self.scheduler = tg.create_task(Scheduler().run())
            self.shell = tg.create_task(Shell().run())

    async def shutdown(self) -> None:
        print("Shutting down")
        self.shell.cancel()
        self.scheduler.cancel()
        print("Shutdown complete")
