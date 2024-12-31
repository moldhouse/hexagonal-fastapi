import asyncio
import sys
from asyncio import Future, Queue
from typing import NamedTuple, Protocol

from src.worker import WorkerApi, WorkerResponse


class CompletionTask(NamedTuple):
    """Internal representation of a completion task."""

    prompt: str
    future: Future[
        WorkerResponse
    ]  # future is used to send the result back to the caller


class SchedulerApi(Protocol):
    async def complete(self, prompt: str) -> WorkerResponse: ...


class Scheduler(SchedulerApi):
    """Batch completion jobs and send them to a worker."""

    def __init__(self, worker: WorkerApi, max_wait_time: float) -> None:
        """Initialize the scheduler.

        Args:
            worker: The worker to send completion tasks to.
            max_wait_time: Maximum time in seconds a completion requests needs to wait
                for other tasks to join its batch.
        """
        self.incoming: Queue[CompletionTask] = Queue()
        self.scheduled: list[CompletionTask] = []
        self.worker = worker
        self.tasks: list[asyncio.Task[None]] = []
        self.max_wait_time = max_wait_time

    async def complete(self, prompt: str) -> WorkerResponse:
        """Complete a given prompt."""
        future: Future[WorkerResponse] = Future()
        await self.incoming.put(CompletionTask(prompt, future))
        return await future

    async def run(self) -> None:
        """Schedule a worker run for existing completion tasks.

        Tasks are scheduled to run in batches of 8. If no tasks are incoming,
        existing tasks never have to wait more than `max_wait_time` seconds.
        """
        loop = asyncio.get_running_loop()
        self.next_run: int | float = sys.maxsize
        while True:
            try:
                async with asyncio.timeout_at(self.next_run):
                    task = await self.incoming.get()

                if len(self.scheduled) == 0:
                    self.next_run = loop.time() + self.max_wait_time
                self.scheduled.append(task)
            except asyncio.TimeoutError:
                pass
            except asyncio.QueueShutDown:
                break

            if len(self.scheduled) == 8 or loop.time() >= self.next_run:
                self.tasks.append(
                    asyncio.create_task(self.complete_batch(self.scheduled))
                )
                self.scheduled = []
                self.next_run = sys.maxsize

    async def complete_batch(self, messages: list[CompletionTask]) -> None:
        """Complete a batch of messages by sending them to the worker.

        The results are returned to the original caller.
        """
        results = await self.worker.complete([message.prompt for message in messages])
        for message, result in zip(messages, results):
            message.future.set_result(result)

    def shutdown(self) -> None:
        """Gracefully shut down the scheduler."""
        self.incoming.shutdown()
        for task in self.tasks:
            task.cancel()
