from unittest import IsolatedAsyncioTestCase

from news_fastapi.adapters.persistence.tortoise.transaction import (
    TortoiseTransactionManager,
)
from news_fastapi.core.events.registry import DomainEventHandlerRegistry
from news_fastapi.domain.seed_work.events import DomainEvent, DomainEventBuffer
from tests.adapters.persistence.tortoise.fixtures import tortoise_orm_lifespan
from tests.domain.seed_work.test_events import TestDomainEvent


class TestEventHandler:
    called_with_event: DomainEvent | None = None

    async def __call__(self, event: DomainEvent) -> None:
        self.called_with_event = event


class TortoiseTransactionManagerTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.domain_event_buffer = DomainEventBuffer()
        self.domain_event_handler_registry = DomainEventHandlerRegistry()
        self.transaction_manager = TortoiseTransactionManager(
            domain_event_buffer=self.domain_event_buffer,
            domain_event_handler_registry=self.domain_event_handler_registry,
        )

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    async def test_commit_dispatches_domain_events(self) -> None:
        event = TestDomainEvent(answer=42)
        self.domain_event_buffer.append(event)
        event_handler = TestEventHandler()
        self.domain_event_handler_registry.register(
            event_type=TestDomainEvent, event_handler=event_handler
        )
        async with self.transaction_manager.in_transaction():
            pass
        self.assertIs(event_handler.called_with_event, event)
