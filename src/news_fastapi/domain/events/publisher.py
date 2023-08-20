from abc import ABC, abstractmethod
from uuid import uuid4


class DomainEventIdGenerator(ABC):
    @abstractmethod
    async def next_event_id(self) -> str:
        raise NotImplementedError


class UUID4DomainEventIdGenerator(DomainEventIdGenerator):
    async def next_event_id(self) -> str:
        return str(uuid4())
