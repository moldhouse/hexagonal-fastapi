import asyncio

from src.config import AppConfig
from src.scheduler import Scheduler
from src.shell import Shell
from src.worker import StubWorker


class App:
    """The application runs the scheduler and the shell."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            worker = StubWorker()
            self.scheduler = Scheduler(worker, max_wait_time=1.0)
            self.shell = Shell(self.config, self.scheduler)

            tg.create_task(self.scheduler.run())
            tg.create_task(self.shell.run())

    def shutdown(self) -> None:
        self.shell.shutdown()
        self.scheduler.shutdown()
