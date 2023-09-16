from unittest import IsolatedAsyncioTestCase

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from news_fastapi.adapters.persistence.sqlalchemy_orm_naive.models import Model
from news_fastapi.adapters.persistence.sqlalchemy_orm_naive.transaction import (
    SQLAlchemyORMTransactionManager,
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
        self.domain_event_buffer = DomainEventBuffer()
        self.domain_event_handler_registry = DomainEventHandlerRegistry()

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Model.metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.transaction_manager = SQLAlchemyORMTransactionManager(
            domain_event_dispatcher=DomainEventDispatcher(
                domain_event_buffer=self.domain_event_buffer,
                domain_event_handler_registry=self.domain_event_handler_registry,
            ),
            session=self.session,
        )

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

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
