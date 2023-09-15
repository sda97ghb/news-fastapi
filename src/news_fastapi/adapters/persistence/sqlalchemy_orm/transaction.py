from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from news_fastapi.core.transaction import (
    DomainEventDispatcher,
    TransactionContextManager,
    TransactionManager,
)


class SQLAlchemyORMTransactionManager(TransactionManager):
    _domain_event_dispatcher: DomainEventDispatcher
    _session: AsyncSession

    def __init__(
        self,
        domain_event_dispatcher: DomainEventDispatcher,
        session: AsyncSession,
    ) -> None:
        self._domain_event_dispatcher = domain_event_dispatcher
        self._session = session

    def in_transaction(self) -> TransactionContextManager:
        return self._in_transaction()

    @asynccontextmanager
    async def _in_transaction(self):
        async with self._session.begin():
            yield
            await self._domain_event_dispatcher.dispatch()
