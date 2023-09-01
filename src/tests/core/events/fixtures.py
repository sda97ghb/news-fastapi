from dataclasses import dataclass
from typing import Any

from news_fastapi.domain.events import DomainEvent


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
