from contextlib import asynccontextmanager

from anyio import create_task_group
from tortoise.transactions import in_transaction

from news_fastapi.core.events.registry import DomainEventHandlerRegistry
from news_fastapi.core.transaction import TransactionContextManager, TransactionManager
from news_fastapi.domain.events import DomainEventBuffer


class TortoiseTransactionManager(TransactionManager):
    _domain_event_buffer: DomainEventBuffer
    _domain_event_handler_registry: DomainEventHandlerRegistry

    def __init__(
        self,
        domain_event_buffer: DomainEventBuffer,
        domain_event_handler_registry: DomainEventHandlerRegistry,
    ) -> None:
        self._domain_event_buffer = domain_event_buffer
        self._domain_event_handler_registry = domain_event_handler_registry

    def in_transaction(self) -> TransactionContextManager:
        return self._in_transaction()

    @asynccontextmanager
    async def _in_transaction(self):
        async with in_transaction():
            yield
            await self._dispatch_domain_events()

    async def _dispatch_domain_events(self) -> None:
        events = self._domain_event_buffer.complete()
        for event in events:
            handlers = self._domain_event_handler_registry.get_handlers(type(event))
            async with create_task_group() as task_group:
                for handler in handlers:
                    task_group.start_soon(handler, event)
