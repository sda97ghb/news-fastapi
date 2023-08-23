from dependency_injector.wiring import Provide

from news_fastapi.core.drafts.services import DraftsService
from news_fastapi.domain.authors import AuthorDeleted
from news_fastapi.domain.events.server import EventHandlerRegistry

domain_event_handler_registry = EventHandlerRegistry()


@domain_event_handler_registry.on(AuthorDeleted)
async def on_author_deleted_delete_drafts(
    event: AuthorDeleted, drafts_service: DraftsService = Provide["draft_service"]
) -> None:
    await drafts_service.delete_drafts_of_author(event.author_id)
