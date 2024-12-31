from typing import NamedTuple, Protocol


class CompletionResponse(NamedTuple):
    completion: str
    tokens: int


class WorkerApi(Protocol):
    """A worker that can complete prompts.

    Might be an `Ollama` or `vLLM` process on the same machine.
    Invocation could be over HTTP.
    """

    async def complete(self, prompts: list[str]) -> list[CompletionResponse]: ...


class StubWorker(WorkerApi):
    """Stub worker implementation that returns the prompt as the completion."""

    async def complete(self, prompts: list[str]) -> list[CompletionResponse]:
        return [
            CompletionResponse(completion=prompt, tokens=len(prompt))
            for prompt in prompts
        ]
