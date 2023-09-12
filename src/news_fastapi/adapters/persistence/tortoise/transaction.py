from contextlib import asynccontextmanager

from tortoise.transactions import in_transaction

from news_fastapi.core.events.registry import DomainEventHandlerRegistry
from news_fastapi.core.transaction import (
    DomainEventDispatcher,
    TransactionContextManager,
    TransactionManager,
)
from news_fastapi.domain.seed_work.events import DomainEventBuffer


class TortoiseTransactionManager(TransactionManager):
    _domain_event_dispatcher: DomainEventDispatcher

    def __init__(
        self,
        domain_event_buffer: DomainEventBuffer,
        domain_event_handler_registry: DomainEventHandlerRegistry,
    ) -> None:
        self._domain_event_dispatcher = DomainEventDispatcher(
            domain_event_buffer=domain_event_buffer,
            domain_event_handler_registry=domain_event_handler_registry,
        )

    def in_transaction(self) -> TransactionContextManager:
        return self._in_transaction()

    @asynccontextmanager
    async def _in_transaction(self):
        async with in_transaction():
            yield
            await self._domain_event_dispatcher.dispatch()
