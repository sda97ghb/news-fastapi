import asyncio
from datetime import datetime as DateTime
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock
from uuid import uuid4

from news_fastapi.adapters.events.server import (
    DomainEventPublisher,
    EventHandlerRegistry,
    PublishServer,
)
from tests.adapters.events.fixtures import (
    AnotherTestDomainEvent,
    TestDomainEvent,
    TestDomainEventStore,
    TestPublishChannel,
    mock_another_event_handler,
    mock_event_handler,
)


class EventHandlerRegistryTests(TestCase):
    def setUp(self) -> None:
        self.registry = EventHandlerRegistry()

    def test_register(self) -> None:
        self.registry.register(
            event_type=TestDomainEvent, event_handler=mock_event_handler
        )
        handlers = self.registry.get_handlers(TestDomainEvent)
        self.assertCountEqual(handlers, [mock_event_handler])

    def test_on(self) -> None:
        decorator = self.registry.on(TestDomainEvent)
        decorator(mock_event_handler)
        handlers = self.registry.get_handlers(TestDomainEvent)
        self.assertCountEqual(handlers, [mock_event_handler])

    def test_extend(self) -> None:
        another_registry = EventHandlerRegistry()
        another_registry.register(
            event_type=TestDomainEvent, event_handler=mock_event_handler
        )
        self.registry.extend(another_registry)
        handlers = self.registry.get_handlers(TestDomainEvent)
        self.assertCountEqual(handlers, [mock_event_handler])

    def test_get_handlers_returns_all_handlers(self) -> None:
        self.registry.register(
            event_type=TestDomainEvent, event_handler=mock_event_handler
        )
        self.registry.register(
            event_type=TestDomainEvent, event_handler=mock_another_event_handler
        )
        handlers = self.registry.get_handlers(TestDomainEvent)
        self.assertCountEqual(
            handlers, [mock_event_handler, mock_another_event_handler]
        )

    def test_get_handlers_returns_handlers_of_appropriate_type(self) -> None:
        self.registry.register(
            event_type=TestDomainEvent, event_handler=mock_event_handler
        )
        self.registry.register(
            event_type=AnotherTestDomainEvent, event_handler=mock_another_event_handler
        )
        handlers = self.registry.get_handlers(TestDomainEvent)
        self.assertCountEqual(handlers, [mock_event_handler])


class DomainEventPublisherTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.domain_event_store = TestDomainEventStore()
        self.publish_channel = TestPublishChannel()
        self.publisher = DomainEventPublisher(
            publish_channels=[self.publish_channel],
            domain_event_store=self.domain_event_store,
            send_batch_size=50,
        )

    async def test_publish(self) -> None:
        event = TestDomainEvent(
            event_id=str(uuid4()),
            date_occurred=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
        )
        await self.domain_event_store.append(event)
        await self.publisher.publish()
        self.assertCountEqual(self.publish_channel.published_events, [event])


class PublishServerTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.publisher = AsyncMock()
        self.server = PublishServer(publisher=self.publisher)

    async def test_run(self) -> None:
        self.server.start()
        self.server.should_publish_domain_events_flag.set()
        await asyncio.sleep(1)
        await self.server.stop()
        self.assertFalse(self.server.should_publish_domain_events_flag.is_set())
        self.publisher.publish.assert_awaited()

    async def test_immediately_stop_does_not_raise(self) -> None:
        self.server.start()
        await self.server.stop()

    async def test_does_not_publish_before_started(self) -> None:
        # server is created in setUp but not started
        await asyncio.sleep(1)
        self.publisher.publish.assert_not_awaited()

    async def test_does_not_publish_after_stop(self) -> None:
        self.server.start()
        await asyncio.sleep(1)
        await self.server.stop()
        self.publisher.publish.reset_mock()
        await asyncio.sleep(1)
        self.publisher.publish.assert_not_awaited()
