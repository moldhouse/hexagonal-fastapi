import asyncio

from src.app import App
from src.config import AppConfig


async def test_app_can_be_shutdown():
    # Given a running app
    config = AppConfig.with_free_port()
    app = App(config)
    task = asyncio.create_task(app.run())
    await asyncio.sleep(0.01)

    # When we shutdown the app
    app.shutdown()

    # Then the task completes
    await asyncio.wait_for(task, timeout=1.0)
