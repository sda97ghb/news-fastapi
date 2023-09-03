from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Image:
    url: str
    description: str
    author: str
