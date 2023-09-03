from dataclasses import dataclass
from typing import Any

from news_fastapi.domain.seed_work.events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class TestDomainEvent(DomainEvent):
    def _to_json_extra_fields(self) -> dict[str, Any]:
        return {}


@dataclass(kw_only=True, frozen=True)
class AnotherTestDomainEvent(DomainEvent):
    def _to_json_extra_fields(self) -> dict[str, Any]:
        return {}


async def mock_event_handler(event: DomainEvent) -> None:
    pass


async def mock_another_event_handler(event: DomainEvent) -> None:
    pass
