from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_session
from app.repositories.products import ProductRepository
from app.schemas.products import ProductCreate, ProductRead, ProductUpdate
from app.services.products import ProductService

router = APIRouter()


def get_service(request: Request, session: AsyncSession = Depends(get_session)) -> ProductService:
    redis: Redis = request.app.state.redis
    return ProductService(
        repository=ProductRepository(session),
        redis=redis,
    )


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    service: ProductService = Depends(get_service),
):
    try:
        return await service.create(payload)
    except Exception as exc:
        # Не раскрываем клиенту внутренние детали инфраструктуры.
        # В production ошибки нужно логировать с correlation ID и разделять по типам.
        raise HTTPException(status_code=503, detail="Could not complete product creation") from exc


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    service: ProductService = Depends(get_service),
):
    product = await service.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    service: ProductService = Depends(get_service),
):
    try:
        product = await service.update(product_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not complete product update") from exc

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/{product_id}", response_model=ProductRead)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_service)
):
    try:
        product = await service.delete(product_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not complete product delete") from exc
    
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product