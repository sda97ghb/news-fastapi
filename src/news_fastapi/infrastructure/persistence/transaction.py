from asyncio import Event as AsyncIOEvent
from contextlib import asynccontextmanager

from tortoise.transactions import in_transaction

from news_fastapi.application.transaction import (
    TransactionContextManager,
    TransactionManager,
)


class TortoiseTransactionManager(TransactionManager):
    _should_send_domain_events_flag: AsyncIOEvent

    def __init__(self, should_send_domain_events_flag: AsyncIOEvent) -> None:
        self._should_send_domain_events_flag = should_send_domain_events_flag

    def in_transaction(self) -> TransactionContextManager:
        return self._in_transaction()

    @asynccontextmanager
    async def _in_transaction(self):
        async with in_transaction():
            yield
        self._should_send_domain_events_flag.set()
