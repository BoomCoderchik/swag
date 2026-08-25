from dataclasses import dataclass, field


@dataclass
class Item:
    source: str
    title: str
    url: str
    description: str = ""
    metrics: str = ""
    tags: list[str] = field(default_factory=list)
    published_ts: float | None = None
