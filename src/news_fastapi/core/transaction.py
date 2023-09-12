from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Any

from anyio import create_task_group

from news_fastapi.core.events.registry import DomainEventHandlerRegistry
from news_fastapi.domain.seed_work.events import DomainEventBuffer

TransactionContextManager = AbstractAsyncContextManager[Any]


class TransactionManager(ABC):
    @abstractmethod
    def in_transaction(self) -> TransactionContextManager:
        raise NotImplementedError


class DomainEventDispatcher:
    _domain_event_buffer: DomainEventBuffer
    _domain_event_handler_registry: DomainEventHandlerRegistry

    def __init__(
        self,
        domain_event_buffer: DomainEventBuffer,
        domain_event_handler_registry: DomainEventHandlerRegistry,
    ) -> None:
        self._domain_event_buffer = domain_event_buffer
        self._domain_event_handler_registry = domain_event_handler_registry

    async def dispatch(self) -> None:
        events = self._domain_event_buffer.complete()
        for event in events:
            handlers = self._domain_event_handler_registry.get_handlers(type(event))
            async with create_task_group() as task_group:
                for handler in handlers:
                    task_group.start_soon(handler, event)
