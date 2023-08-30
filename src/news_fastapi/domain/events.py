from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime as DateTime
from json import dumps as dumps_json
from typing import Any, Collection
from uuid import uuid4


@dataclass
class DomainEvent(ABC):
    event_id: str
    date_occurred: DateTime

    @property
    def type_name(self) -> str:
        return type(self).__name__

    def to_json(self) -> dict:
        return {
            "event_type": self.type_name,
            "event_id": self.event_id,
            "date_occurred": self.date_occurred.isoformat(),
            **self._to_json_extra_fields(),
        }

    @abstractmethod
    def _to_json_extra_fields(self) -> dict[str, Any]:
        raise NotImplementedError

    def to_json_str(self) -> str:
        return dumps_json(self.to_json())


class DomainEventStore(ABC):
    @abstractmethod
    async def append(self, event: DomainEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_not_sent_events(self, limit: int) -> Collection[DomainEvent]:
        raise NotImplementedError

    @abstractmethod
    async def ack_event_send(self, event: DomainEvent) -> None:
        raise NotImplementedError


class DomainEventIdGenerator(ABC):
    @abstractmethod
    async def next_event_id(self) -> str:
        raise NotImplementedError


class UUID4DomainEventIdGenerator(DomainEventIdGenerator):
    async def next_event_id(self) -> str:
        return str(uuid4())
