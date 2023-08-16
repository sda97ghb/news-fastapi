from tortoise.transactions import in_transaction

from news_fastapi.application.core.transaction import (
    TransactionContextManager,
    TransactionManager,
)


class TortoiseTransactionManager(TransactionManager):
    def in_transaction(self) -> TransactionContextManager:
        return in_transaction()
