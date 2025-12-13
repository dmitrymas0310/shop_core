from uuid import UUID
from datetime import datetime
from typing import List, Optional
from fastapi import Depends, HTTPException, status

from app.promotions.repository import PromotionRepository
from app.promotions.schemas import (
    PromotionCreate, PromotionUpdate, PromotionRead,
    PromotionWithProducts, AttachProductsRequest
)
from app.catalog.repository import ProductRepository, get_product_repository
from app.core.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession


def get_promotion_repository(db: AsyncSession = Depends(get_session)) -> PromotionRepository:
    return PromotionRepository(db)


class PromotionService:
    def __init__(
            self,
            promotion_repo: PromotionRepository,
            product_repo: ProductRepository
    ):
        self.promotion_repo = promotion_repo
        self.product_repo = product_repo

    async def create_promotion(self, data: PromotionCreate) -> PromotionRead:
        """Создание новой акции"""
        # Валидация дат
        if data.ends_at <= data.starts_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        promotion = await self.promotion_repo.create_promotion(
            title=data.title,
            description=data.description,
            discount_percent=data.discount_percent,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            is_active=data.is_active
        )

        return PromotionRead.model_validate(promotion)

    async def get_promotion(self, promotion_id: UUID) -> PromotionWithProducts:
        """Получение акции по ID с товарами"""
        promotion = await self.promotion_repo.get_promotion_by_id(promotion_id)

        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )

        # Собираем ID товаров
        product_ids = [pp.product_id for pp in promotion.promotion_products]
        
        result = PromotionWithProducts.model_validate(promotion)
        result.product_ids = product_ids
        return result

    async def get_all_promotions(
            self,
            limit: int = 100,
            skip: int = 0,
            is_active: Optional[bool] = None
    ) -> List[PromotionRead]:
        """Получение списка всех акций"""
        promotions = await self.promotion_repo.get_all_promotions(
            limit=limit,
            skip=skip,
            is_active=is_active
        )
        return [PromotionRead.model_validate(p) for p in promotions]

    async def get_active_promotions(self) -> List[PromotionWithProducts]:
        """Получение активных акций (для гостей и пользователей)"""
        promotions = await self.promotion_repo.get_active_promotions()
        result = []
        for promotion in promotions:
            promo_data = PromotionWithProducts.model_validate(promotion)
            promo_data.product_ids = [pp.product_id for pp in promotion.promotion_products]
            result.append(promo_data)
        return result

    async def update_promotion(
            self,
            promotion_id: UUID,
            data: PromotionUpdate
    ) -> PromotionRead:
        """Обновление акции"""
        promotion = await self.promotion_repo.get_promotion_by_id(promotion_id)

        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )

        # Валидация дат если они обновляются
        starts_at = data.starts_at if data.starts_at is not None else promotion.starts_at
        ends_at = data.ends_at if data.ends_at is not None else promotion.ends_at
        
        if ends_at <= starts_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        update_data = data.model_dump(exclude_unset=True)
        updated_promotion = await self.promotion_repo.update_promotion(
            promotion_id=promotion_id,
            **update_data
        )

        return PromotionRead.model_validate(updated_promotion)

    async def delete_promotion(self, promotion_id: UUID) -> dict:
        """Удаление акции"""
        promotion = await self.promotion_repo.get_promotion_by_id(promotion_id)

        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )

        deleted = await self.promotion_repo.delete_promotion(promotion_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete promotion"
            )

        return {"message": "Promotion deleted successfully"}

    async def attach_products(
            self,
            promotion_id: UUID,
            data: AttachProductsRequest
    ) -> PromotionWithProducts:
        """Привязка товаров к акции"""
        promotion = await self.promotion_repo.get_promotion_by_id(promotion_id)

        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )

        # Проверяем существование всех товаров
        for product_id in data.product_ids:
            product = await self.product_repo.get_product_by_id(product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {product_id} not found"
                )

        # Привязываем товары
        await self.promotion_repo.attach_products_to_promotion(
            promotion_id=promotion_id,
            product_ids=data.product_ids
        )

        # Возвращаем обновленную акцию
        return await self.get_promotion(promotion_id)

    async def detach_products(
            self,
            promotion_id: UUID,
            data: AttachProductsRequest
    ) -> PromotionWithProducts:
        """Отвязка товаров от акции"""
        promotion = await self.promotion_repo.get_promotion_by_id(promotion_id)

        if not promotion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Promotion not found"
            )

        await self.promotion_repo.detach_products_from_promotion(
            promotion_id=promotion_id,
            product_ids=data.product_ids
        )

        return await self.get_promotion(promotion_id)


def get_promotion_service(
        promotion_repo: PromotionRepository = Depends(get_promotion_repository),
        product_repo: ProductRepository = Depends(get_product_repository)
) -> PromotionService:
    return PromotionService(promotion_repo, product_repo)
