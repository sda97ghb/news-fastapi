News FastAPI
============

# Architecture

This project use Hexagonal Architecture and DDD.

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
of infrastructure level.

### `news_fastapi.adapters`

Various adapters as defined in Hexagonal Architecture.

### `news_fastapi.adapters.auth`

Implements authentication and authorization.

### `news_fastapi.adapters.persistence`

All persistence related implementations, i.e. implements repositories, queries, etc.

### `news_fastapi.adapters.persistence.tortoise`

Persistence related code implemented with TortoiseORM.

### `news_fastapi.adapters.rest_api`

REST API controllers.

### `news_fastapi.main`

`news_fastapi.main.asgi` contains ASGI application definition.

`news_fastapi.main.container` IOC container, dependency root.

`news_fastapi.main.*` another application entrypoints, usually auxiliary CLI scripts.

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
