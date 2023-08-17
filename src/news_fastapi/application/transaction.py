from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Any

TransactionContextManager = AbstractAsyncContextManager[Any]


class TransactionManager(ABC):
    @abstractmethod
    def in_transaction(self) -> TransactionContextManager:
        raise NotImplementedError
