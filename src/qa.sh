#!/usr/bin/env bash
isort .
black .
mypy news_fastapi
pylint --rcfile ../pyproject.toml news_fastapi
