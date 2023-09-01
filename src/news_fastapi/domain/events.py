from abc import ABC, abstractmethod
from dataclasses import dataclass, field as dataclass_field
from datetime import UTC, datetime as DateTime
from json import dumps as dumps_json
from typing import Any, Iterable
from uuid import uuid4


@dataclass(kw_only=True)
class DomainEvent(ABC):
    event_id: str = dataclass_field(default_factory=lambda: str(uuid4()))
    date_occurred: DateTime = dataclass_field(default_factory=lambda: DateTime.now(UTC))

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


class CompleteDomainEventBufferError(Exception):
    pass


class DomainEventBuffer:
    _events: list[DomainEvent]
    _is_complete: bool

    def __init__(self) -> None:
        self._events = []
        self._is_complete = False

    def append(self, event: DomainEvent) -> None:
        if self._is_complete:
            raise CompleteDomainEventBufferError(
                "Can not append event into complete buffer"
            )
        self._events.append(event)

    def complete(self) -> Iterable[DomainEvent]:
        self._is_complete = True
        return self._events
