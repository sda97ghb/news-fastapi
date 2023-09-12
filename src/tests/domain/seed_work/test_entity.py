from unittest import IsolatedAsyncioTestCase, TestCase
from uuid import UUID

from news_fastapi.domain.seed_work.entity import Entity, Repository


class Cat(Entity):
    _name: str

    def __init__(self, id_: str, name: str) -> None:
        super().__init__(id_)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name


class Dog(Entity):
    _name: str

    def __init__(self, id_: str, name: str) -> None:
        super().__init__(id_)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name


class EntityTests(TestCase):
    def test_equals(self) -> None:
        luna = Cat(id_="11111111-1111-1111-1111-111111111111", name="Luna")
        bella = Cat(id_="11111111-1111-1111-1111-111111111111", name="Bella")
        self.assertEqual(luna, bella)

    def test_equals_none_is_not_equal(self) -> None:
        luna = Cat(id_="11111111-1111-1111-1111-111111111111", name="Luna")
        self.assertNotEqual(luna, None)

    def test_equals_not_instance_of_entity_is_not_equal(self) -> None:
        luna = Cat(id_="11111111-1111-1111-1111-111111111111", name="Luna")
        self.assertNotEqual(luna, object())

    def test_equals_self_is_equal(self) -> None:
        luna = Cat(id_="11111111-1111-1111-1111-111111111111", name="Luna")
        self.assertEqual(luna, luna)

    def test_equals_instance_of_different_entity_is_not_equal(self) -> None:
        luna = Cat(id_="11111111-1111-1111-1111-111111111111", name="Luna")
        charlie = Dog(id_="11111111-1111-1111-1111-111111111111", name="Charlie")
        self.assertNotEqual(luna, charlie)


class CatRepository(Repository):
    pass


class RepositoryTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = CatRepository()

    async def test_next_identity(self) -> None:
        id_1 = await self.repository.next_identity()
        id_2 = await self.repository.next_identity()
        for id_ in [id_1, id_2]:
            try:
                UUID(id_)
            except ValueError:
                self.fail(f"next_identity returned badly formed UUID: {id_}")
        self.assertNotEqual(id_1, id_2)
