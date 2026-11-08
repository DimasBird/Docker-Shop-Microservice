from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1000)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0, le=1000)


class CartItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    product_name: str
    unit_price: Decimal
    subtotal: Decimal


class CartRead(BaseModel):
    items: list[CartItemRead]
    total_amount: Decimal