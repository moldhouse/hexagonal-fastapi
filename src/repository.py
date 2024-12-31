"""Store information about token usage.

An actual implementation would connect to a database.

```python
from sqlalchemy.ext.asyncio import create_async_engine


class PostgresRepository(Repository):
    def __init__(self) -> None:
        self.engine = create_async_engine("connection_string", pool_size=5)

    async def store_token_usage(self, user_id: int, tokens: int) -> None:
        async with self.engine.begin() as connection:
            await connection.execute(
                "INSERT INTO token_usage (user_id, tokens) VALUES ($1, $2)", user_id, tokens
            )
```
"""

from typing import Protocol


class Repository(Protocol):
    async def store_token_usage(self, user_id: int, tokens: int) -> None: ...


class StubRepository(Repository):
    def __init__(self) -> None:
        self.data: dict[int, int] = {}

    async def store_token_usage(self, user_id: int, tokens: int) -> None:
        if user_id not in self.data:
            self.data[user_id] = tokens
        else:
            self.data[user_id] += tokens
