from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import CartItem, Product
from app.db.postgres import get_session
from app.schemas.cart import CartItemCreate, CartItemUpdate

from app.api.dependencies import get_current_user_id


router = APIRouter()


@router.get("")
async def get_cart(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    result = await session.execute(
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.product))
    )
    items = result.scalars().all()

    response_items = []
    total = Decimal("0.00")

    for item in items:
        price = item.product.price
        subtotal = price * item.quantity
        total += subtotal

        response_items.append({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "product_name": item.product.name,
            "unit_price": price,
            "subtotal": subtotal,
        })

    return {"items": response_items, "total_amount": total}


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    payload: CartItemCreate,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    product = await session.get(Product, payload.product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    result = await session.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == payload.product_id,
        )
    )
    item = result.scalar_one_or_none()

    if item is None:
        item = CartItem(
            user_id=user_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        session.add(item)
    else:
        new_quantity = item.quantity + payload.quantity

        if new_quantity > 1000:
            raise HTTPException(
                status_code=422,
                detail="Maximum quantity exceeded",
            )

        item.quantity = new_quantity

    await session.commit()
    return {"status": "ok"}


@router.patch("/items/{product_id}")
async def update_cart_item(
    product_id: int,
    payload: CartItemUpdate,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    result = await session.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
        )
    )
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    item.quantity = payload.quantity
    await session.commit()

    return {"status": "ok"}


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    product_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    result = await session.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
        )
    )
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    await session.delete(item)
    await session.commit()