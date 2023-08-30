from collections.abc import Sized
from uuid import UUID


class AssertMixin:
    def assertEmpty(self, sized: Sized) -> None:
        self.assertEqual(len(sized), 0)

    def assertNotEmpty(self, sized: Sized) -> None:
        self.assertGreater(len(sized), 0)

    def assertValidUUID(self, id_: str) -> None:
        try:
            UUID(id_)
        except ValueError:
            self.fail(f"invalid UUID value {id_!r}")
