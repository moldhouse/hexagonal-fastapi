import asyncio
import sys
from asyncio import Future, Queue
from typing import NamedTuple, Protocol

from pydantic import BaseModel

from src.repository import Repository
from src.worker import CompletionResponse, WorkerApi


class CompletionRequest(BaseModel):
    prompt: str
    user_id: int


class CompletionTask(NamedTuple):
    """Internal representation of a completion task."""

    request: CompletionRequest
    future: Future[CompletionResponse]


class SchedulerApi(Protocol):
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...


class Scheduler(SchedulerApi):
    """Batch completion jobs and send them to a worker."""

    BATCH_SIZE: int = 8
    MAX_WAIT_TIME: float = 0.1  # seconds

    def __init__(self, worker: WorkerApi, repository: Repository) -> None:
        """Initialize the scheduler.

        Args:
            worker: The worker to send completion tasks to.
            repository: Stores token usage
        """
        self.worker = worker
        self.repository = repository
        self.incoming: Queue[CompletionTask] = Queue()
        self.scheduled: list[CompletionTask] = []
        self.worker_tasks: list[asyncio.Task[None]] = []

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Complete a given prompt."""
        future: Future[CompletionResponse] = Future()
        await self.incoming.put(CompletionTask(request, future))
        return await future

    async def run(self) -> None:
        """Schedule a worker run for existing completion tasks.

        Tasks are scheduled to run in batches. If no tasks are incoming,
        existing tasks never have to wait more than `MAX_WAIT_TIME` seconds.
        """
        loop = asyncio.get_running_loop()
        self.next_run: int | float = sys.maxsize
        while True:
            try:
                async with asyncio.timeout_at(self.next_run):
                    task = await self.incoming.get()

                if len(self.scheduled) == 0:
                    self.next_run = loop.time() + self.MAX_WAIT_TIME
                self.scheduled.append(task)
            except asyncio.TimeoutError:
                pass
            except asyncio.QueueShutDown:
                break

            if len(self.scheduled) == self.BATCH_SIZE or loop.time() >= self.next_run:
                self.worker_tasks.append(
                    asyncio.create_task(self.complete_batch(self.scheduled))
                )
                self.scheduled = []
                self.next_run = sys.maxsize

    async def complete_batch(self, tasks: list[CompletionTask]) -> None:
        """Complete a batch of messages by sending them to the worker.

        The results are returned to the original caller.
        """
        results = await self.worker.complete([task.request.prompt for task in tasks])
        for task, result in zip(tasks, results):
            task.future.set_result(result)
            await self.repository.store_token_usage(task.request.user_id, result.tokens)

    def shutdown(self) -> None:
        """Gracefully shut down the scheduler."""
        self.incoming.shutdown()
        for task in self.worker_tasks:
            task.cancel()
