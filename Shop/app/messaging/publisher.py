import json

import aio_pika

from app.core.config import settings


async def publish_product_event(event: dict) -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        queue = await channel.declare_queue(
            "product-events",
            durable=True,
            arguments={"x-queue-type": "quorum"}
        )
        message = aio_pika.Message(
            body=json.dumps(event).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await channel.default_exchange.publish(
            message,
            routing_key=queue.name,
        )
    finally:
        await connection.close()
