from dataclasses import dataclass
from typing import Any, Collection

from news_fastapi.adapters.events.server import PublishChannel
from news_fastapi.domain.events import DomainEvent, DomainEventStore


@dataclass
class TestDomainEvent(DomainEvent):
    def _to_json_extra_fields(self) -> dict[str, Any]:
        return {}


class AnotherTestDomainEvent(DomainEvent):
    def _to_json_extra_fields(self) -> dict[str, Any]:
        return {}


async def mock_event_handler(event: DomainEvent) -> None:
    pass


async def mock_another_event_handler(event: DomainEvent) -> None:
    pass


class TestPublishChannel(PublishChannel):
    published_events: list[DomainEvent]

    def __init__(self) -> None:
        self.published_events = []

    async def publish(self, event: DomainEvent) -> None:
        self.published_events.append(event)


class TestDomainEventStore(DomainEventStore):
    _events: list[DomainEvent]

    def __init__(self) -> None:
        self._events = []

    async def append(self, event: DomainEvent) -> None:
        self._events.append(event)

    async def get_not_sent_events(self, limit: int) -> Collection[DomainEvent]:
        return self._events[:limit]

    async def ack_event_send(self, event: DomainEvent) -> None:
        try:
            self._events.remove(event)
        except ValueError:
            pass
