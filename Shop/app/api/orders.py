from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import CartItem, Order, OrderItem
from app.db.postgres import get_session
from app.schemas.orders import OrderRead

from app.api.dependencies import get_current_user_id


router = APIRouter()


@router.post("", response_model=OrderRead, status_code=201)
async def create_order(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    try:
        result = await session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
            .with_for_update()
        )
        cart_items = list(result.scalars().all())

        if not cart_items:
            raise HTTPException(
                status_code=400,
                detail="Cart is empty",
            )

        total = Decimal("0.00")
        order_items = []

        for cart_item in cart_items:
            product = cart_item.product

            if product is None:
                raise HTTPException(
                    status_code=400,
                    detail="A product in the cart no longer exists",
                )
            
            if cart_item.quantity > cart_item.product.stock:
                raise HTTPException(
                    status_code=409,
                    detail=f"Not enough stock for product {cart_item.product_id}",
                )

            price = product.price
            total += price * cart_item.quantity

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=cart_item.quantity,
                    unit_price=price,
                )
            )

        order = Order(
            user_id=user_id,
            status="created",
            total_amount=total,
            items=order_items,
        )
        session.add(order)

        # Заказ создаётся и корзина очищается в одной транзакции.
        for cart_item in cart_items:
            await session.delete(cart_item)

        await session.flush()
        await session.refresh(order)
        await session.commit()

        # Загружаем позиции заказа после сохранения.
        result = await session.execute(
            select(Order)
            .where(
                Order.id == order.id,
                Order.user_id == user_id,
            )
            .options(selectinload(Order.items))
        )
        return result.scalar_one()

    except HTTPException:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise


@router.get("", response_model=list[OrderRead])
async def get_orders(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    result = await session.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    result = await session.execute(
        select(Order)
        .where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order