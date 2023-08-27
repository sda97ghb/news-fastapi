from collections.abc import Sized


class AssertMixin:
    def assertIsEmpty(self, sized: Sized) -> None:
        self.assertEqual(len(sized), 0)
