from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthorReference(Protocol):
    id: str


@runtime_checkable
class Author(Protocol):
    id: str
    name: str


@dataclass
class AuthorReferenceDataclass:
    id: str

    def __check_implements_protocol(self) -> AuthorReference:
        return self


@dataclass
class AuthorDataclass:
    id: str
    name: str

    def __check_implements_protocol(self) -> Author:
        return self
