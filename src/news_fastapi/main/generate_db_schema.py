import asyncio

from tortoise import Tortoise

from news_fastapi.main.container import DIContainer

di_container = DIContainer()
di_container.config.from_dict(
    {
        "db": {
            "url": "sqlite:////tmp/news_fastapi.sqlite3",
        }
    }
)


async def main() -> None:
    tortoise_config: dict = di_container.tortoise_config()
    print(type(tortoise_config), tortoise_config)
    await Tortoise.init(config=tortoise_config)
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()


if __name__ == "__main__":
    di_container.wire()
    asyncio.run(main())
