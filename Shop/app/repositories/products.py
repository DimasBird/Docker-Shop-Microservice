from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product
from app.schemas.products import ProductCreate, ProductUpdate


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payload: ProductCreate) -> Product:
        product = Product(**payload.model_dump())
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self, product: Product, payload: ProductUpdate
    ) -> Product:
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(product, field, value)
        await self.session.commit()
        await self.session.refresh(product)
        return product
    
    async def delete(
            self, product_id: int
    ) -> bool:
        product = await self.get(product_id)

        if product is not None:
            await self.session.delete(product)
            await self.session.commit()

        return product
