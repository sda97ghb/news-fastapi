from dataclasses import dataclass

from news_fastapi.domain.authors import Author, AuthorFactory


@dataclass
class AuthorDataclass:
    id: str  # pylint: disable=invalid-name
    name: str

    def __assert_implements_protocol(self) -> Author:
        # pylint: disable=unused-private-member
        return self


class DataclassesAuthorFactory(AuthorFactory):
    def create_author(self, author_id: str, name: str) -> Author:
        return AuthorDataclass(id=author_id, name=name)
