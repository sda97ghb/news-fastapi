import aiormq
from aiormq import AMQPError
from aiormq.abc import AbstractConnection

from news_fastapi.adapters.events.server import PublishChannel
from news_fastapi.domain.events import DomainEvent


class RabbitMQConnectionFactory:
    _url: str

    def __init__(self, url: str) -> None:
        self._url = url

    async def connect(self) -> AbstractConnection:
        return await aiormq.connect(url=self._url)


class RabbitMQPublishChannel(PublishChannel):
    _connection_factory: RabbitMQConnectionFactory
    _connection: AbstractConnection | None

    def __init__(self, connection_factory: RabbitMQConnectionFactory) -> None:
        self._connection_factory = connection_factory

    async def publish(self, event: DomainEvent) -> None:
        if self._connection is None:
            self._connection = await self._connection_factory.connect()

        try:
            channel = await self._connection.channel()

            exchange = "domain-events"
            await channel.exchange_declare(exchange=exchange, exchange_type="topic")

            body = self._serialize_event(event)
            await channel.basic_publish(
                body=body,
                exchange=exchange,
                routing_key=f"domain.{event.type_name}",
            )
        except AMQPError:
            self._connection = None
            raise

    def _serialize_event(self, event: DomainEvent) -> bytes:
        return event.to_json_str().encode("utf-8")

    async def close(self) -> None:
        if self._connection is None:
            return
        await self._connection.close()
