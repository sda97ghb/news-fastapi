class CreateDraftError(Exception):
    pass


class CreateDraftConflictError(Exception):
    news_article_id: str
    draft_id: str
    created_by_user_id: str

    def __init__(
        self, news_article_id: str, draft_id: str, created_by_user_id: str
    ) -> None:
        super().__init__(
            "News article already has a draft, "
            "publish or delete this draft before creating new one"
        )
        self.news_article_id = news_article_id
        self.draft_id = draft_id
        self.created_by_user_id = created_by_user_id


class UpdateDraftError(Exception):
    pass


class DeleteDraftError(Exception):
    pass
