from news_fastapi.main.container import DIContainer

di_container = DIContainer()
di_container.config.from_dict(
    {
        "db": {
            "url": "sqlite:////tmp/news_fastapi.sqlite3",
        },
        "fastapi": {
            "debug": True,
            "cors": {
                "allow_origins": ["http://localhost:4000"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            },
        },
    }
)
di_container.wire()

app = di_container.asgi_app()
