from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"^\S(?:.*\S)?$")
    description: str = Field(default="", max_length=5000)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock: int = Field(default=0, ge=0, le=1_000_000)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120, pattern=r"^\S(?:.*\S)?$")
    description: str | None = Field(default=None, max_length=5000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock: int | None = Field(default=None, ge=0, le=1_000_000)


class ProductRead(BaseModel):
    id: int
    name: str
    description: str
    price: Decimal
    stock: int

    model_config = ConfigDict(from_attributes=True)
