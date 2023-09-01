from unittest import TestCase

from news_fastapi.core.events.registry import DomainEventHandlerRegistry
from tests.core.events.fixtures import (
    AnotherTestDomainEvent,
    TestDomainEvent,
    mock_another_event_handler,
    mock_event_handler,
)


class EventHandlerRegistryTests(TestCase):
    def setUp(self) -> None:
        self.registry = DomainEventHandlerRegistry()

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
        another_registry = DomainEventHandlerRegistry()
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
