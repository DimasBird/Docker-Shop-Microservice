from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.api.products import router as products_router
from app.core.config import settings
from app.db.models import Base
from app.db.postgres import engine

from app.api.cart import router as cart_router
from app.api.orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Учебный bootstrap. Перед серьёзным использованием заменить на миграции Alembic.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis.ping()
    app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()
        await engine.dispose()


app = FastAPI(
    title="Secure Shop API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


app.include_router(products_router, prefix="/products", tags=["products"])


app.include_router(cart_router, prefix="/cart", tags=["cart"])
app.include_router(orders_router, prefix="/orders", tags=["orders"])