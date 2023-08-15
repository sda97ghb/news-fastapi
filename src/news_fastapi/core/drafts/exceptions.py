class CreateDraftError(Exception):
    pass


class CreateDraftConflictError(Exception):
    news_id: str
    draft_id: str
    created_by_user_id: str

    def __init__(self, news_id: str, draft_id: str, created_by_user_id: str) -> None:
        super().__init__(
            f"News already has draft, publish or delete it before creating new one"
        )
        self.news_id = news_id
        self.draft_id = draft_id
        self.created_by_user_id = created_by_user_id


class UpdateDraftError(Exception):
    pass


class DeleteDraftError(Exception):
    pass


class AlreadyPublishedError(Exception):
    pass
