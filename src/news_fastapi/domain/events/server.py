import asyncio
from asyncio import (
    CancelledError,
    Event as AsyncIOEvent,
    Task,
    create_task as create_asyncio_task,
)
from collections import defaultdict
from collections.abc import AsyncIterable, Awaitable, Callable, Collection
from datetime import datetime as DateTime

from anyio import create_task_group

from news_fastapi.domain.authors import AuthorDeleted
from news_fastapi.domain.events.models import DomainEvent

DomainEventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventHandlerRegistry:
    _handlers: dict[type[DomainEvent], set[DomainEventHandler]]

    def __init__(self) -> None:
        self._handlers = defaultdict(set)

    def on(self, event_type: type[DomainEvent]):
        def decorator(event_handler: DomainEventHandler):
            self.register(event_type, event_handler)
            return event_handler

        return decorator

    def register(
        self, event_type: type[DomainEvent], event_handler: DomainEventHandler
    ) -> None:
        self._handlers[event_type].add(event_handler)

    def extend(self, another: "EventHandlerRegistry") -> None:
        # pylint: disable=protected-access
        for event_type, handlers in another._handlers.items():
            self._handlers[event_type] |= handlers

    def get_handlers(
        self, event_type: type[DomainEvent]
    ) -> Collection[DomainEventHandler]:
        return self._handlers[event_type]


class DomainEventServer:
    _listen_task: Task | None
    _send_task: Task | None
    _event_handler_registry: EventHandlerRegistry
    _event_stream: AsyncIterable[DomainEvent]
    _should_send_domain_events_flag: AsyncIOEvent

    def __init__(self, event_stream: AsyncIterable[DomainEvent]) -> None:
        self._listen_task = None
        self._send_task = None
        self._event_handler_registry = EventHandlerRegistry()
        self._event_stream = event_stream
        self._should_send_domain_events_flag = AsyncIOEvent()

    @property
    def should_send_domain_events_flag(self) -> AsyncIOEvent:
        return self._should_send_domain_events_flag

    def include_registry(self, registry: EventHandlerRegistry) -> None:
        self._event_handler_registry.extend(registry)

    def start(self) -> None:
        self.start_listen()
        self.start_send()

    def start_listen(self) -> None:
        if self._listen_task is None:
            self._listen_task = create_asyncio_task(self._run_listen())

    def start_send(self) -> None:
        if self._send_task is None:
            self._send_task = create_asyncio_task(self._run_send())
            self._should_send_domain_events_flag.set()

    async def stop(self) -> None:
        await self.stop_listen()
        await self.stop_send()

    async def stop_listen(self) -> None:
        if self._listen_task is not None:
            self._listen_task.cancel()
            await self._listen_task
            self._listen_task = None

    async def stop_send(self) -> None:
        if self._send_task is not None:
            self._send_task.cancel()
            await self._send_task
            self._send_task = None

    async def _run_listen(self) -> None:
        async with create_task_group() as task_group:
            async for event in self._event_stream:
                event_type = type(event)
                handlers = self._event_handler_registry.get_handlers(event_type)
                for handler in handlers:
                    task_group.start_soon(self._run_handler, handler, event)

    async def _run_handler(
        self, handler: DomainEventHandler, event: DomainEvent
    ) -> None:
        try:
            await handler(event)
        except CancelledError:  # pylint: disable=try-except-raise
            raise
        except Exception as err:  # pylint: disable=broad-exception-caught
            print(f"Exception in handler: {err}")

    async def _run_send(self) -> None:
        try:
            while await self._should_send_domain_events_flag.wait():
                self._should_send_domain_events_flag.clear()
                await self._send()
        except CancelledError:
            pass

    async def _send(self) -> None:
        # TODO: send
        ...


if __name__ == "__main__":
    event_handler_registry = EventHandlerRegistry()

    @event_handler_registry.on(AuthorDeleted)
    async def on_author_deleted_print(event: AuthorDeleted) -> None:
        print(f"Author deleted {event.author_id}")

    @event_handler_registry.on(AuthorDeleted)
    async def long_handler(event: AuthorDeleted) -> None:
        print(f"long started {event.author_id}")
        await asyncio.sleep(int(event.author_id))
        print(f"long finished {event.author_id}")

    async def mock_event_stream():
        yield AuthorDeleted(event_id="1", date_occurred=DateTime.now(), author_id="1")
        yield AuthorDeleted(event_id="2", date_occurred=DateTime.now(), author_id="3")
        yield AuthorDeleted(event_id="3", date_occurred=DateTime.now(), author_id="5")

    server = DomainEventServer(event_stream=mock_event_stream())
    server.include_registry(event_handler_registry)

    async def main():
        server.start()

        await asyncio.sleep(4)

        await server.stop()
        print("main completed successfully")

    asyncio.run(main())
