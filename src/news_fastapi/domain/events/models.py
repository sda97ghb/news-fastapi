from dataclasses import dataclass
from datetime import datetime as DateTime


@dataclass
class DomainEvent:
    event_id: str
    date_occurred: DateTime
