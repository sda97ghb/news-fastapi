from collections import defaultdict
from collections.abc import Awaitable, Callable, Collection

from news_fastapi.domain.seed_work.events import DomainEvent

DomainEventHandler = Callable[[DomainEvent], Awaitable[None]]


class DomainEventHandlerRegistry:
    _handlers: dict[type[DomainEvent], set[DomainEventHandler]]

    def __init__(self) -> None:
        self._handlers = defaultdict(set)

    def on(self, event_type: type[DomainEvent]):
        def decorator(event_handler: DomainEventHandler):
            self.register(event_type, event_handler)
            return event_handler

        return decorator

    def register(
        self, event_type: type[DomainEvent], event_handler: DomainEventHandler
    ) -> None:
        self._handlers[event_type].add(event_handler)

    def extend(self, another: "DomainEventHandlerRegistry") -> None:
        # pylint: disable=protected-access
        for event_type, handlers in another._handlers.items():
            self._handlers[event_type] |= handlers

    def get_handlers(
        self, event_type: type[DomainEvent]
    ) -> Collection[DomainEventHandler]:
        return self._handlers[event_type]
