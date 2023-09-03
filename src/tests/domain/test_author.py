from datetime import datetime as DateTime
from unittest import TestCase

from news_fastapi.domain.author import Author, AuthorDeleted, AuthorFactory


class AuthorTests(TestCase):
    def setUp(self) -> None:
        self.author = Author(
            id_="11111111-1111-1111-1111-111111111111", name="John Doe"
        )

    def test_set_name(self) -> None:
        new_name = "James Smith"
        self.author.name = new_name
        self.assertEqual(self.author.name, new_name)

    def test_set_name_to_empty_string_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.author.name = ""


class AuthorFactoryTests(TestCase):
    def setUp(self) -> None:
        self.factory = AuthorFactory()

    def test_create_author(self) -> None:
        author_id = "11111111-1111-1111-1111-111111111111"
        name = "John Doe"
        author = self.factory.create_author(author_id=author_id, name=name)
        self.assertEqual(author.id, author_id)
        self.assertEqual(author.name, name)


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
