from dataclasses import dataclass


@dataclass
class AuthorOverview:
    id: str
    name: str


@dataclass
class AuthorDetails:
    id: str
    name: str
