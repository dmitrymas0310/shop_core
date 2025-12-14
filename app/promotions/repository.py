from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from app.promotions.models import Promotion, PromotionProduct


class PromotionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_promotion(
            self,
            title: str,
            description: Optional[str],
            discount_percent: float,
            starts_at: datetime,
            ends_at: datetime,
            is_active: bool = True
    ) -> Promotion:
        promotion = Promotion(
            title=title,
            description=description,
            discount_percent=discount_percent,
            starts_at=starts_at,
            ends_at=ends_at,
            is_active=is_active
        )
        self.db.add(promotion)
        await self.db.commit()
        await self.db.refresh(promotion)
        return promotion

    async def get_promotion_by_id(self, promotion_id: UUID) -> Optional[Promotion]:
        result = await self.db.execute(
            select(Promotion)
            .options(selectinload(Promotion.promotion_products))
            .where(Promotion.id == promotion_id)
        )
        return result.scalar_one_or_none()

    async def get_all_promotions(
            self,
            limit: int = 100,
            skip: int = 0,
            is_active: Optional[bool] = None
    ) -> List[Promotion]:
        query = select(Promotion).options(selectinload(Promotion.promotion_products))
        
        if is_active is not None:
            query = query.where(Promotion.is_active == is_active)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_promotions(self) -> List[Promotion]:
        """Получить активные акции, которые сейчас действуют"""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Promotion)
            .options(selectinload(Promotion.promotion_products))
            .where(
                and_(
                    Promotion.is_active == True,
                    Promotion.starts_at <= now,
                    Promotion.ends_at >= now
                )
            )
        )
        return list(result.scalars().all())

    async def update_promotion(
            self,
            promotion_id: UUID,
            **kwargs
    ) -> Optional[Promotion]:
        # Удаляем None значения
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_promotion_by_id(promotion_id)

        await self.db.execute(
            update(Promotion)
            .where(Promotion.id == promotion_id)
            .values(**update_data)
        )
        await self.db.commit()
        return await self.get_promotion_by_id(promotion_id)

    async def delete_promotion(self, promotion_id: UUID) -> bool:
        result = await self.db.execute(
            delete(Promotion).where(Promotion.id == promotion_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    # Методы для работы с PromotionProduct
    async def attach_products_to_promotion(
            self,
            promotion_id: UUID,
            product_ids: List[UUID]
    ) -> List[PromotionProduct]:
        """Привязать товары к акции"""
        promotion_products = []
        for product_id in product_ids:
            # Проверяем, не существует ли уже такая связь
            existing = await self.db.execute(
                select(PromotionProduct).where(
                    and_(
                        PromotionProduct.promotion_id == promotion_id,
                        PromotionProduct.product_id == product_id
                    )
                )
            )
            if existing.scalar_one_or_none() is None:
                pp = PromotionProduct(
                    promotion_id=promotion_id,
                    product_id=product_id
                )
                self.db.add(pp)
                promotion_products.append(pp)
        
        await self.db.commit()
        return promotion_products

    async def detach_products_from_promotion(
            self,
            promotion_id: UUID,
            product_ids: List[UUID]
    ) -> bool:
        """Отвязать товары от акции"""
        result = await self.db.execute(
            delete(PromotionProduct).where(
                and_(
                    PromotionProduct.promotion_id == promotion_id,
                    PromotionProduct.product_id.in_(product_ids)
                )
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_promotion_products(
            self,
            promotion_id: UUID
    ) -> List[PromotionProduct]:
        """Получить все связи товаров с акцией"""
        result = await self.db.execute(
            select(PromotionProduct)
            .where(PromotionProduct.promotion_id == promotion_id)
        )
        return list(result.scalars().all())

    async def get_product_promotions(
            self,
            product_id: UUID
    ) -> List[Promotion]:
        """Получить все акции для товара"""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Promotion)
            .join(PromotionProduct)
            .where(
                and_(
                    PromotionProduct.product_id == product_id,
                    Promotion.is_active == True,
                    Promotion.starts_at <= now,
                    Promotion.ends_at >= now
                )
            )
        )
        return list(result.scalars().all())
