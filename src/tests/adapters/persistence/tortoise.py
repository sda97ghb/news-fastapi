from contextlib import asynccontextmanager

from tortoise import Tortoise


@asynccontextmanager
async def tortoise_orm():
    tortoise_config = dict(
        connections=dict(
            default="sqlite://:memory:",
        ),
        apps=dict(
            news_fastapi=dict(
                models=[
                    "news_fastapi.adapters.persistence.authors",
                    "news_fastapi.adapters.persistence.drafts",
                    "news_fastapi.adapters.persistence.events",
                    "news_fastapi.adapters.persistence.news",
                ]
            )
        ),
    )
    await Tortoise.init(config=tortoise_config)
    await Tortoise.generate_schemas()
    try:
        yield
    finally:
        await Tortoise.close_connections()
