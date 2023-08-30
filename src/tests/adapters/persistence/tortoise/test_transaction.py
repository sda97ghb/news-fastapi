from asyncio import Event as AsyncIOEvent
from unittest import IsolatedAsyncioTestCase

from news_fastapi.adapters.persistence.tortoise.transaction import (
    TortoiseTransactionManager,
)
from tests.adapters.persistence.tortoise.fixtures import tortoise_orm_lifespan


class TortoiseTransactionManagerTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.should_send_domain_events_flag = AsyncIOEvent()
        self.transaction_manager = TortoiseTransactionManager(
            should_send_domain_events_flag=self.should_send_domain_events_flag
        )

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    async def test_commit_sets_should_send_domain_events_flag(self) -> None:
        self.should_send_domain_events_flag.clear()
        async with self.transaction_manager.in_transaction():
            pass
        self.assertTrue(self.should_send_domain_events_flag.is_set())
