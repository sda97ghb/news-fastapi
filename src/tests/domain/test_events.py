from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Any
from unittest import IsolatedAsyncioTestCase, TestCase

from news_fastapi.domain.events import DomainEvent, UUID4DomainEventIdGenerator
from tests.utils import AssertMixin


@dataclass
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


class UUID4DomainEventIdGeneratorTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.generator = UUID4DomainEventIdGenerator()

    async def test_next_event_id_returns_valid_uuid(self) -> None:
        id_ = await self.generator.next_event_id()
        self.assertValidUUID(id_)

    async def test_next_event_id_returns_different_ids(self) -> None:
        id_1 = await self.generator.next_event_id()
        id_2 = await self.generator.next_event_id()
        self.assertNotEqual(id_1, id_2)
