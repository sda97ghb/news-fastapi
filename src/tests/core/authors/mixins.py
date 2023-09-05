class AuthorTestsMixin:
    async def _populate_author(self) -> str:
        author_id = "22222222-2222-2222-2222-222222222222"
        author_to_save = self.author_factory.create_author(
            author_id=author_id, name="John Doe"
        )
        await self.author_repository.save(author_to_save)
        return author_id
