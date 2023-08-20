import asyncio
from asyncio import Task

from anyio import create_task_group


async def handle_event(event_id: int, handler_id: int) -> None:
    raise Exception("intended to fail")
    try:
        print("handle_event started", event_id, handler_id)
        await asyncio.sleep(event_id)
        print("handle_event finished", event_id, handler_id)
    except asyncio.CancelledError:
        print("handle_event cancelled", event_id, handler_id)
        raise


class EventServer:
    _task: Task | None

    def __init__(self) -> None:
        self._task = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            await self._task
            self._task = None

    async def _run(self) -> None:
        async with create_task_group() as tg:
            for event_id in range(10):
                for handler_id in range(5):
                    # tg.start_soon(handle_event, event_id, handler_id)
                    tg.start_soon(self._run_handler, handle_event, event_id, handler_id)

    async def _run_handler(self, handler, event_id, handler_id) -> None:
        try:
            await handler(event_id, handler_id)
        except asyncio.CancelledError:
            raise
        except Exception as err:
            print(f"Exception in handler: {err}")


async def main():
    event_server = EventServer()
    event_server.start()

    await asyncio.sleep(4)

    await event_server.stop()
    print("main(): EventServer.run is cancelled now")


asyncio.run(main())
