from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Any
from unittest import TestCase

from news_fastapi.domain.seed_work.events import (
    CompleteDomainEventBufferError,
    DomainEvent,
    DomainEventBuffer,
)


@dataclass(kw_only=True, frozen=True)
class TestDomainEvent(DomainEvent):
    answer: int

    def _to_json_extra_fields(self) -> dict[str, Any]:
        return {"answer": self.answer}


class DomainEventTests(TestCase):
    def setUp(self) -> None:
        self.event = TestDomainEvent(
            event_id="11111111-1111-1111-1111-111111111111",
            date_occurred=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            answer=42,
        )

    def test_type_name(self) -> None:
        self.assertEqual(self.event.type_name, "TestDomainEvent")

    def test_to_json(self) -> None:
        self.assertEqual(
            self.event.to_json(),
            {
                "event_type": "TestDomainEvent",
                "event_id": "11111111-1111-1111-1111-111111111111",
                "date_occurred": "2023-01-01T12:00:00+00:00",
                "answer": 42,
            },
        )

    def test_to_json_str(self) -> None:
        self.assertEqual(
            self.event.to_json_str(),
            "{"
            '"event_type": "TestDomainEvent", '
            '"event_id": "11111111-1111-1111-1111-111111111111", '
            '"date_occurred": "2023-01-01T12:00:00+00:00", '
            '"answer": 42'
            "}",
        )


class DomainEventBufferTests(TestCase):
    def setUp(self) -> None:
        self.buffer = DomainEventBuffer()

    def test_lifecycle(self) -> None:
        event_1 = TestDomainEvent(answer=42)
        event_2 = TestDomainEvent(answer=10)
        self.buffer.append(event_1)
        self.buffer.append(event_2)
        events = self.buffer.complete()
        self.assertCountEqual(events, [event_1, event_2])

    def test_can_not_append_after_complete(self) -> None:
        self.buffer.complete()
        with self.assertRaises(CompleteDomainEventBufferError):
            self.buffer.append(TestDomainEvent(answer=42))
