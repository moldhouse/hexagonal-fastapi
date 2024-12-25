from typing import Protocol


class WorkerApi(Protocol):
    """A worker that can complete prompts.

    Might be an `Ollama` or `vLLM` process on the same machine
    or a remote service. Assume an async interface is used.
    """

    async def complete(self, prompts: list[str]) -> list[str]: ...


class StubWorker(WorkerApi):
    """Stub worker implementation that returns the prompt as the completion."""

    async def complete(self, prompts: list[str]) -> list[str]:
        return [prompt for prompt in prompts]
