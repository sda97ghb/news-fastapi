from abc import ABC, abstractmethod
from asyncio import (
    CancelledError,
    Event as AsyncIOEvent,
    Task,
    create_task as create_asyncio_task,
)
from collections import defaultdict
from collections.abc import AsyncIterable, Awaitable, Callable, Collection

from anyio import create_task_group

from news_fastapi.domain.events import DomainEvent, DomainEventStore

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


class PublishChannel(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        raise NotImplementedError


class DomainEventPublisher:
    _publish_channels: list[PublishChannel]
    _domain_event_store: DomainEventStore
    _publish_batch_size: int

    def __init__(
        self,
        publish_channels: list[PublishChannel],
        domain_event_store: DomainEventStore,
        send_batch_size: int = 50,
    ) -> None:
        self._publish_channels = publish_channels
        self._domain_event_store = domain_event_store
        self._publish_batch_size = send_batch_size

    async def publish(self) -> None:
        while events := await self._get_next_batch_to_publish():
            async with create_task_group() as task_group:
                for event in events:
                    task_group.start_soon(self._publish_event, event)

    async def _get_next_batch_to_publish(self) -> Collection[DomainEvent]:
        return await self._domain_event_store.get_not_sent_events(
            limit=self._publish_batch_size
        )

    async def _publish_event(self, event: DomainEvent) -> None:
        try:
            async with create_task_group() as task_group:
                for publish_channel in self._publish_channels:
                    task_group.start_soon(publish_channel.publish, event)
        except:  # pylint: disable=bare-except
            # just don't ack the event if any error happen
            # in this case the event will be retried
            pass
        else:
            await self._domain_event_store.ack_event_send(event)


class PublishServer:
    _publisher: DomainEventPublisher
    _should_publish_domain_events_flag: AsyncIOEvent
    _task: Task | None

    def __init__(self, publisher: DomainEventPublisher) -> None:
        self._publisher = publisher
        self._should_publish_domain_events_flag = AsyncIOEvent()
        self._task = None

    @property
    def should_publish_domain_events_flag(self) -> AsyncIOEvent:
        return self._should_publish_domain_events_flag

    def start(self) -> None:
        if self._task is None:
            self._task = create_asyncio_task(self._run())
            self._should_publish_domain_events_flag.set()

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        while await self._should_publish_domain_events_flag.wait():
            self._should_publish_domain_events_flag.clear()
            await self._publisher.publish()


class DomainEventListener:
    async def run(self) -> None:
        ...


class DomainEventServer:
    _listen_task: Task | None
    _publish_task: Task | None
    _event_handler_registry: EventHandlerRegistry
    _event_stream: AsyncIterable[DomainEvent]
    _should_send_domain_events_flag: AsyncIOEvent
    _domain_event_store: DomainEventStore
    _send_batch_size: int
    _publish_server: PublishServer

    def __init__(
        self,
        event_stream: AsyncIterable[DomainEvent],
        domain_event_store: DomainEventStore,
        publish_server: PublishServer,
    ) -> None:
        self._listen_task = None
        self._publish_task = None
        self._event_handler_registry = EventHandlerRegistry()
        self._event_stream = event_stream
        self._should_send_domain_events_flag = AsyncIOEvent()
        self._domain_event_store = domain_event_store
        self._send_batch_size = 50
        self._publish_server = publish_server

    @property
    def should_send_domain_events_flag(self) -> AsyncIOEvent:
        return self._publish_server.should_publish_domain_events_flag

    def include_registry(self, registry: EventHandlerRegistry) -> None:
        self._event_handler_registry.extend(registry)

    def start(self) -> None:
        self.start_listen()
        self._publish_server.start()

    def start_listen(self) -> None:
        if self._listen_task is None:
            self._listen_task = create_asyncio_task(self._run_listen())

    async def stop(self) -> None:
        await self.stop_listen()
        await self._publish_server.stop()

    async def stop_listen(self) -> None:
        if self._listen_task is not None:
            self._listen_task.cancel()
            await self._listen_task
            self._listen_task = None

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


# if __name__ == "__main__":
#     event_handler_registry = EventHandlerRegistry()
#
#     @event_handler_registry.on(AuthorDeleted)
#     async def on_author_deleted_print(event: AuthorDeleted) -> None:
#         print(f"Author deleted {event.author_id}")
#
#     @event_handler_registry.on(AuthorDeleted)
#     async def long_handler(event: AuthorDeleted) -> None:
#         print(f"long started {event.author_id}")
#         await asyncio.sleep(int(event.author_id))
#         print(f"long finished {event.author_id}")
#
#     async def mock_event_stream():
#         yield AuthorDeleted(event_id="1", date_occurred=DateTime.now(), author_id="1")
#         yield AuthorDeleted(event_id="2", date_occurred=DateTime.now(), author_id="3")
#         yield AuthorDeleted(event_id="3", date_occurred=DateTime.now(), author_id="5")
#
#     server = DomainEventServer(event_stream=mock_event_stream())
#     server.include_registry(event_handler_registry)
#
#     async def main():
#         server.start()
#
#         await asyncio.sleep(4)
#
#         await server.stop()
#         print("main completed successfully")
#
#     asyncio.run(main())
