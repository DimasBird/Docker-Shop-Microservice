import asyncio
import json
import logging

import aio_pika

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secure_shop.consumer")


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(
            "product-events",
            durable=True,
            arguments={"x-queue-type": "quorum"}
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    event = json.loads(message.body.decode("utf-8"))
                    logger.info("Received product event: %s", event)
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
