import asyncio

from src.scheduler import App

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    app = App()

    try:
        loop.run_until_complete(app.run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(app.shutdown())
        loop.close()
