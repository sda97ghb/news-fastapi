from abc import ABC, abstractmethod
from collections.abc import Collection

from news_fastapi.domain.events.models import DomainEvent


class DomainEventStore(ABC):
    @abstractmethod
    async def append(self, event: DomainEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_not_sent_events(self) -> Collection[DomainEvent]:
        raise NotImplementedError

    @abstractmethod
    async def ack_event_send(self, event: DomainEvent) -> None:
        raise NotImplementedError
