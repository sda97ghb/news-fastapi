from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection

from news_fastapi.core.transaction import (
    DomainEventDispatcher,
    TransactionContextManager,
    TransactionManager,
)


class SQLAlchemyTransactionManager(TransactionManager):
    _domain_event_dispatcher: DomainEventDispatcher
    _connection: AsyncConnection

    def __init__(
        self,
        domain_event_dispatcher: DomainEventDispatcher,
        connection: AsyncConnection,
    ) -> None:
        self._domain_event_dispatcher = domain_event_dispatcher
        self._connection = connection

    def in_transaction(self) -> TransactionContextManager:
        return self._in_transaction()

    @asynccontextmanager
    async def _in_transaction(self):
        async with self._connection.begin():
            yield
            await self._domain_event_dispatcher.dispatch()
