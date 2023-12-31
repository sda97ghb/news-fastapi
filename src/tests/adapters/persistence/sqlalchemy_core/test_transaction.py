from unittest import IsolatedAsyncioTestCase

from sqlalchemy.ext.asyncio import create_async_engine

from news_fastapi.adapters.persistence.sqlalchemy_core.tables import metadata
from news_fastapi.adapters.persistence.sqlalchemy_core.transaction import (
    SQLAlchemyTransactionManager,
)
from news_fastapi.core.events.registry import DomainEventHandlerRegistry
from news_fastapi.core.transaction import DomainEventDispatcher
from news_fastapi.domain.seed_work.events import DomainEvent, DomainEventBuffer
from tests.domain.seed_work.test_events import TestDomainEvent


class TestEventHandler:
    called_with_event: DomainEvent | None = None

    async def __call__(self, event: DomainEvent) -> None:
        self.called_with_event = event


class TortoiseTransactionManagerTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")
        self.engine.execution_options()
        self.domain_event_buffer = DomainEventBuffer()
        self.domain_event_handler_registry = DomainEventHandlerRegistry()

    async def asyncSetUp(self) -> None:
        self.connection = await self.engine.connect()
        await self.connection.begin()
        await self.connection.run_sync(metadata.create_all)
        await self.connection.commit()
        self.transaction_manager = SQLAlchemyTransactionManager(
            domain_event_dispatcher=DomainEventDispatcher(
                domain_event_buffer=self.domain_event_buffer,
                domain_event_handler_registry=self.domain_event_handler_registry,
            ),
            connection=self.connection,
        )

    async def asyncTearDown(self) -> None:
        await self.connection.close()

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
