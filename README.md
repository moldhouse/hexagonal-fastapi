# Hexagonal FastAPI

A scheduler that collects incoming completion requests and send them in batches to a worker. Used to explore hexagonal architecture patterns and the `asyncio` module.

## Getting Started

```sh
uv sync
```

Run the scheduler with

```sh
uv run python -m src.main
```

Run the tests with

```sh
uv run pytest
```