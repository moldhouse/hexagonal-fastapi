from typing import NamedTuple, Protocol


class WorkerResponse(NamedTuple):
    completion: str
    tokens: int


class WorkerApi(Protocol):
    """A worker that can complete prompts.

    Might be an `Ollama` or `vLLM` process on the same machine.
    Invocation could be over HTTP.
    """

    async def complete(self, prompts: list[str]) -> list[WorkerResponse]: ...


class StubWorker(WorkerApi):
    """Stub worker implementation that returns the prompt as the completion."""

    async def complete(self, prompts: list[str]) -> list[WorkerResponse]:
        return [
            WorkerResponse(completion=prompt, tokens=len(prompt)) for prompt in prompts
        ]
