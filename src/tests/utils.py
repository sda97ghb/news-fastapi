from collections.abc import Sized


class AssertMixin:
    def assertEmpty(self, sized: Sized) -> None:
        self.assertEqual(len(sized), 0)

    def assertNotEmpty(self, sized: Sized) -> None:
        self.assertGreater(len(sized), 0)
