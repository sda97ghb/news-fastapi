from tortoise.transactions import in_transaction

from news_fastapi.application.transaction import (
    TransactionContextManager,
    TransactionManager,
)


class TortoiseTransactionManager(TransactionManager):
    def in_transaction(self) -> TransactionContextManager:
        return in_transaction()
