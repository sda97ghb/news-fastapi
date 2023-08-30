from enum import StrEnum
from typing import Collection

from tortoise import Model
from tortoise.fields import BinaryField, BooleanField, DatetimeField, TextField

from news_fastapi.domain.authors import AuthorDeleted
from news_fastapi.domain.events import DomainEvent, DomainEventStore


class TortoiseDomainEvent(Model):
    event_id = TextField(pk=True)
    date_occurred = DatetimeField()
    event_type = TextField()
    body: bytes = BinaryField()
    is_sent = BooleanField()

    class Meta:
        table = "domain_events"


class DomainEventTypeName(StrEnum):
    AUTHOR_DELETED = "AuthorDeleted"


class TortoiseDomainEventStore(DomainEventStore):
    async def append(self, event: DomainEvent) -> None:
        event_type_name, event_body = self._serialize(event)
        stored_event = TortoiseDomainEvent(
            event_id=event.event_id,
            date_occurred=event.date_occurred,
            event_type=event_type_name,
            body=event_body,
            is_sent=False,
        )
        await stored_event.save()

    async def get_not_sent_events(self, limit: int) -> Collection[DomainEvent]:
        events_list = await TortoiseDomainEvent.filter(is_sent=False).limit(limit)
        return [self._parse(event) for event in events_list]

    async def ack_event_send(self, event: DomainEvent) -> None:
        await TortoiseDomainEvent.filter(event_id=event.event_id).update(is_sent=True)

    def _serialize(self, event: DomainEvent) -> tuple[str, bytes]:
        if isinstance(event, AuthorDeleted):
            return (
                DomainEventTypeName.AUTHOR_DELETED,
                event.author_id.encode(encoding="utf-8"),
            )
        raise NotImplementedError(f"Unable to serialize body of {event.__class__}")

    def _parse(self, stored_event: TortoiseDomainEvent) -> DomainEvent:
        if stored_event.event_type == DomainEventTypeName.AUTHOR_DELETED:
            return AuthorDeleted(
                event_id=stored_event.event_id,
                date_occurred=stored_event.date_occurred,
                author_id=stored_event.body.decode(encoding="utf-8"),
            )
        raise NotImplementedError(f"Unable to parse body of {stored_event.event_type}")
