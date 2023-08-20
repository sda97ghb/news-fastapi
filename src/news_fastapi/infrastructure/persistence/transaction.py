from contextlib import asynccontextmanager

from tortoise.transactions import in_transaction

from news_fastapi.application.transaction import (
    TransactionContextManager,
    TransactionManager,
)


class TortoiseTransactionManager(TransactionManager):
    def in_transaction(self) -> TransactionContextManager:
        return self._in_transaction()

    @asynccontextmanager
    async def _in_transaction(self):
        async with in_transaction():
            yield
