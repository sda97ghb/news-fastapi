from contextlib import asynccontextmanager

from tortoise import Tortoise, connections


@asynccontextmanager
async def tortoise_orm_lifespan():
    tortoise_config = dict(
        connections=dict(
            default="sqlite://:memory:",
        ),
        apps=dict(
            news_fastapi=dict(
                models=[
                    "news_fastapi.adapters.persistence.tortoise.authors",
                    "news_fastapi.adapters.persistence.tortoise.drafts",
                    "news_fastapi.adapters.persistence.tortoise.news",
                ],
            ),
        ),
    )
    await Tortoise.init(config=tortoise_config, _create_db=True)
    await Tortoise.generate_schemas(safe=False)
    try:
        yield
    finally:
        await Tortoise._drop_databases()
        await Tortoise.close_connections()
        connections.db_config.clear()
        Tortoise.apps = {}
        Tortoise._inited = False
