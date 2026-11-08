import json

from redis.asyncio import Redis

from app.core.config import settings
from app.messaging.publisher import publish_product_event
from app.repositories.products import ProductRepository
from app.schemas.products import ProductCreate, ProductRead, ProductUpdate


class ProductService:
    def __init__(self, repository: ProductRepository, redis: Redis):
        self.repository = repository
        self.redis = redis

    @staticmethod
    def _cache_key(product_id: int) -> str:
        return f"product:{product_id}"

    async def create(self, payload: ProductCreate) -> ProductRead:
        product = await self.repository.create(payload)
        # Для нового ID кэш обычно ещё не существует, но удаление сохраняет
        # единый порядок действий для create/update.
        await self.redis.delete(self._cache_key(product.id))
        await publish_product_event(
            {"event": "product.created", "product_id": product.id}
        )
        return ProductRead.model_validate(product)

    async def get(self, product_id: int) -> ProductRead | None:
        key = self._cache_key(product_id)
        cached = await self.redis.get(key)
        if cached is not None:
            return ProductRead.model_validate_json(cached)

        product = await self.repository.get(product_id)
        if product is None:
            return None

        result = ProductRead.model_validate(product)
        await self.redis.set(
            key,
            result.model_dump_json(),
            ex=settings.cache_ttl_seconds,
        )
        return result

    async def update(
        self, product_id: int, payload: ProductUpdate
    ) -> ProductRead | None:
        product = await self.repository.get(product_id)
        if product is None:
            return None

        product = await self.repository.update(product, payload)
        await self.redis.delete(self._cache_key(product_id))
        await publish_product_event(
            {"event": "product.updated", "product_id": product_id}
        )
        return ProductRead.model_validate(product)
    
    async def delete(
            self, product_id: int
    ) -> ProductRead | None:
        product = await self.repository.delete(product_id)
        if product is None:
            return None
        
        await self.redis.delete(f"product:{product_id}")

        return product

