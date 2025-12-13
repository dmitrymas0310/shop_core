from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.promotions.service import PromotionService, get_promotion_service
from app.promotions.schemas import (
    PromotionCreate, PromotionUpdate, PromotionRead,
    PromotionWithProducts, AttachProductsRequest
)
from app.auth.service import get_current_user_dep
from app.users.models import User
from app.users.enum import UserRole


router = APIRouter(
    prefix="/promotions",
    tags=["promotions"],
)


# Публичные эндпоинты (доступны всем)
@router.get(
    "/",
    response_model=List[PromotionWithProducts],
    summary="Получить список активных акций"
)
async def get_active_promotions(
        service: PromotionService = Depends(get_promotion_service)
) -> List[PromotionWithProducts]:
    """
    Получить список действующих акций.
    Доступно всем пользователям (Guest, User, Admin).
    """
    return await service.get_active_promotions()


@router.get(
    "/{promotion_id}",
    response_model=PromotionWithProducts,
    summary="Получить информацию об акции"
)
async def get_promotion(
        promotion_id: UUID,
        service: PromotionService = Depends(get_promotion_service)
) -> PromotionWithProducts:
    """
    Получить детальную информацию об акции.
    Доступно всем пользователям.
    """
    return await service.get_promotion(promotion_id)


# Админские эндпоинты
@router.post(
    "/admin",
    response_model=PromotionRead,
    summary="[Админ] Создать новую акцию"
)
async def create_promotion(
        data: PromotionCreate,
        current_user: User = Depends(get_current_user_dep),
        service: PromotionService = Depends(get_promotion_service)
) -> PromotionRead:
    """
    Создать новую акцию.
    Доступно только администраторам.
    """
    if current_user.role != UserRole.ADMIN:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create promotions"
        )
    return await service.create_promotion(data)


@router.get(
    "/admin/all",
    response_model=List[PromotionRead],
    summary="[Админ] Получить все акции"
)
async def get_all_promotions(
        limit: int = Query(100, ge=1, le=1000),
        skip: int = Query(0, ge=0),
        is_active: Optional[bool] = Query(None),
        current_user: User = Depends(get_current_user_dep),
        service: PromotionService = Depends(get_promotion_service)
) -> List[PromotionRead]:
    """
    Получить список всех акций (активных и неактивных).
    Доступно только администраторам.
    """
    if current_user.role != UserRole.ADMIN:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all promotions"
        )
    return await service.get_all_promotions(limit=limit, skip=skip, is_active=is_active)


@router.patch(
    "/admin/{promotion_id}",
    response_model=PromotionRead,
    summary="[Админ] Обновить акцию"
)
async def update_promotion(
        promotion_id: UUID,
        data: PromotionUpdate,
        current_user: User = Depends(get_current_user_dep),
        service: PromotionService = Depends(get_promotion_service)
) -> PromotionRead:
    """
    Обновить существующую акцию.
    Доступно только администраторам.
    """
    if current_user.role != UserRole.ADMIN:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update promotions"
        )
    return await service.update_promotion(promotion_id, data)


@router.delete(
    "/admin/{promotion_id}",
    summary="[Админ] Удалить акцию"
)
async def delete_promotion(
        promotion_id: UUID,
        current_user: User = Depends(get_current_user_dep),
        service: PromotionService = Depends(get_promotion_service)
) -> dict:
    """
    Удалить акцию.
    Доступно только администраторам.
    """
    if current_user.role != UserRole.ADMIN:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete promotions"
        )
    return await service.delete_promotion(promotion_id)


@router.post(
    "/admin/{promotion_id}/products",
    response_model=PromotionWithProducts,
    summary="[Админ] Привязать товары к акции"
)
async def attach_products_to_promotion(
        promotion_id: UUID,
        data: AttachProductsRequest,
        current_user: User = Depends(get_current_user_dep),
        service: PromotionService = Depends(get_promotion_service)
) -> PromotionWithProducts:
    """
    Привязать товары к акции.
    Доступно только администраторам.
    """
    if current_user.role != UserRole.ADMIN:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can attach products to promotions"
        )
    return await service.attach_products(promotion_id, data)


@router.delete(
    "/admin/{promotion_id}/products",
    response_model=PromotionWithProducts,
    summary="[Админ] Отвязать товары от акции"
)
async def detach_products_from_promotion(
        promotion_id: UUID,
        data: AttachProductsRequest,
        current_user: User = Depends(get_current_user_dep),
        service: PromotionService = Depends(get_promotion_service)
) -> PromotionWithProducts:
    """
    Отвязать товары от акции.
    Доступно только администраторам.
    """
    if current_user.role != UserRole.ADMIN:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can detach products from promotions"
        )
    return await service.detach_products(promotion_id, data)
