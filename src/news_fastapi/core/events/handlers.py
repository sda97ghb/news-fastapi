from dependency_injector.wiring import Provide

from news_fastapi.core.drafts.commands import DeleteDraftService
from news_fastapi.core.events.registry import DomainEventHandlerRegistry
from news_fastapi.domain.author import AuthorDeleted

domain_event_handler_registry = DomainEventHandlerRegistry()


@domain_event_handler_registry.on(AuthorDeleted)
async def on_author_deleted_delete_drafts(
    event: AuthorDeleted,
    delete_drafts_service: DeleteDraftService = Provide["delete_draft_service"],
) -> None:
    if not isinstance(event, AuthorDeleted):
        raise TypeError("Expected AuthorDeleted type of event")
    await delete_drafts_service.delete_drafts_of_author(event.author_id)
