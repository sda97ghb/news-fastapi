from datetime import datetime as DateTime
from unittest import TestCase

from news_fastapi.domain.author import AuthorDeleted


class AuthorDeletedTests(TestCase):
    def setUp(self) -> None:
        self.event = AuthorDeleted(
            event_id="11111111-1111-1111-1111-111111111111",
            date_occurred=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="22222222-2222-2222-2222-222222222222",
        )

    def test_to_json(self) -> None:
        self.assertEqual(
            self.event.to_json(),
            {
                "event_type": "AuthorDeleted",
                "event_id": "11111111-1111-1111-1111-111111111111",
                "date_occurred": "2023-01-01T12:00:00+00:00",
                "author_id": "22222222-2222-2222-2222-222222222222",
            },
        )
