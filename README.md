News FastAPI
============

# Architecture

This project uses Hexagonal Architecture and DDD.

## Packages

### `news_fastapi.domain`

DDD related code.

### `news_fastapi.domain.seed_work`

Micro-framework for other domain related code.
See ".NET Microservices: Architecture for Containerized .NET Applications"
section "Seedwork (reusable base classes and interfaces for your domain model)"
https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/seedwork-domain-model-base-classes-interfaces

### `news_fastapi.domain.*`

Aggregates are named by their root entity name without any special suffixes.

`*Factory` classes are factories for aggregates. They are concrete classes
but can be inherited and overriden on infrastructure level.

`*Repository` abstract classes declares repository interface.
They are implemented on infrastructure level.

DomainEvent-based classes are DTO for domain events.

`*Service` classes are responsible for execution of domain-level operations.
Also, domain level services can be defined in any way that fits better
for concrete operation.

### `news_fastapi.domain.value_objects`

Reusable value-objects as they are defined in DDD.

### `news_fastapi.core`

Application core as it is in Hexagonal Architecture.

### `news_fastapi.core.*.command`

`*Service` classes are responsible for execution of commands.

### `news_fastapi.core.*.queries`

`*Queries` abstract classes are responsible for declaration of queries.
These classes are implemented in adapters layer.

`*Service` classes are responsible for execution of queries.

### `news_fastapi.core.*.auth`

`*Auth` abstract classes are responsible for declaration of authorization methods
and methods returning information about current user.

### `news_fastapi.core.*.exceptions` and `news_fastapi.core.exceptions`

Application core level exceptions. Usually raised by command or query services.

### `news_fastapi.core.events`

Defines event handlers for domain events.

### `news_fastapi.core.transaction`

Defines abstract transaction manager interface. This interface is implemented
at infrastructure level.

### `news_fastapi.adapters`

Various adapters as defined in Hexagonal Architecture.

### `news_fastapi.adapters.auth`

Implements authentication and authorization.

### `news_fastapi.adapters.persistence`

All persistence related implementations, i.e. implements repositories, queries, etc.

### `news_fastapi.adapters.persistence.tortoise`

Persistence related code implemented with TortoiseORM.

### `news_fastapi.adapters.persistence.sqlalchemy`

Persistence implemented with SQLAlchemy, partially with Core and 
partially with Imperative Mapping.

This implementation maps database rows directly to entity classes.

Probably, this way is more preferable when used with hexagonal architecture,
because it allows to completely separate entities and persistence and
doesn't introduce any intermediate models. But it also has its own downsides:
since it monkey patches entity classes, it can probably break them and also
heavily depends on implementation details, i.e. protected attributes of entity classes.

### `news_fastapi.adapters.persistence.sqlalchemy_core`

Persistence implemented with SQLAlchemy Core only. No ORM used.

### `news_fastapi.adapeters.persistence.sqlalchemy_orm_naive`

Persistence implemented with SQLAlchemy ORM.

'Naive' here means that ORM maps database rows not to entity classes,
but to intermediate model classes. Then the model classes are manually
mapped to entity classes in repositories.

For direct mapping DB rows to entities see `news_fastapi.adapters.persistence.sqlalchemy`.

### `news_fastapi.adapters.rest_api`

REST API related code: controllers, middleware, ASGI app, etc.

### `news_fastapi.main`

`news_fastapi.main.asgi` constructs ASGI application for ASGI web servers,
such as uvicorn.

`news_fastapi.main.container` IOC container, dependency root.

`news_fastapi.main.*` another application entrypoints, usually auxiliary CLI scripts.

# QA

## Code quality

Run the following commands to check the code quality:

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

# all previous commands can be run at once by qa.sh script
./qa.sh
```

## Tests

```shell
cd src

# all tests
python -m unittest

# tests from single file
python -m unittest tests/path/to/file/test_whatever_you_need.py

# tests from package
python -m unittest discover tests/path/to/package/directory/
```
