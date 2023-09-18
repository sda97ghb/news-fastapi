from dataclasses import dataclass


@dataclass(frozen=True)
class Image:
    url: str
    description: str
    author: str
