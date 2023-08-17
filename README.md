News FastAPI
============


# QA

## Code quality

Run the following commands to ensure the code quality is high enough:

```shell
cd src

# sort imports
isort .

# format code
black .

# check types
mypy news_fastapi

# lint
pylint --rcfile ../pyproject.toml news_fastapi
```
