from uuid import UUID
from decimal import Decimal
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from fastapi import Depends

from app.core.db import get_session
from app.catalog.models import Product, Category


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_product(
            self,
            name: str,
            description: str,
            price: Decimal,
            category_id: Optional[UUID] = None,
            rating: Optional[float] = None
    ) -> Product:
        product = Product(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            rating=rating
        )
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product, ['category'])
        return product

    async def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_all_products(
            self,
            limit: int = 100,
            skip: int = 0
    ) -> List[Product]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_product(
            self,
            product_id: UUID,
            data: Dict[str, Any]
    ) -> Product:
        query = (
            update(Product)
            .where(Product.id == product_id)
            .values(**data)
            .returning(Product)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        product = result.scalar_one()

        await self.db.refresh(product, ['category'])
        return product

    async def delete_product(self, product_id: UUID) -> bool:
        query = delete(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, name: str) -> Category:
        category = Category(name=name)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def get_category_by_id(self, category_id: UUID) -> Optional[Category]:
        result = await self.db.execute(
            select(Category)
            .options(selectinload(Category.products))
            .where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_category_by_name(self, name: str) -> Optional[Category]:
        result = await self.db.execute(
            select(Category)
            .where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all_categories(self, limit: int = 100, skip: int = 0) -> List[Category]:
        result = await self.db.execute(
            select(Category)
            .options(selectinload(Category.products))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_category(
            self,
            category_id: UUID,
            name: str
    ) -> Category:
        result = await self.db.execute(
            update(Category)
            .where(Category.id == category_id)
            .values(name=name)
            .returning(Category)
        )
        await self.db.commit()
        category = result.scalar_one()
        await self.db.refresh(category, ['products'])
        return category

    async def delete_category(self, category_id: UUID) -> bool:
        result = await self.db.execute(
            delete(Category).where(Category.id == category_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        query = select(Category.id).where(Category.name == name)

        if exclude_id:
            query = query.where(Category.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None


async def get_product_repository(db: AsyncSession = Depends(get_session)) -> ProductRepository:
    return ProductRepository(db)


async def get_category_repository(db: AsyncSession = Depends(get_session)) -> CategoryRepository:
    return CategoryRepository(db)