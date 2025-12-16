from uuid import UUID
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.catalog.service import (
    ProductService, CategoryService,
    get_product_service, get_category_service
)
from app.catalog.schemas import (
    ProductCreate, ProductUpdate, ProductRead,
    CategoryCreate, CategoryUpdate, CategoryRead
)
from app.auth.service import get_current_user_dep
from app.users.models import User
from app.users.enum import UserRole

router = APIRouter()


@router.get(
    "/products",
    response_model=List[ProductRead],
    summary="Получить список товаров"
)
async def get_products(
    limit: int = Query(10, ge=1, le=10),
    skip: int = Query(0, ge=0),
    service: ProductService = Depends(get_product_service)
) -> List[ProductRead]:
    return await service.get_products(limit=limit, skip=skip)


@router.get(
    "/products/{product_id}",
    response_model=ProductRead,
    summary="Получить информацию о товаре"
)
async def get_product(
        product_id: UUID,
        service: ProductService = Depends(get_product_service)
) -> ProductRead:
    return await service.get_product(product_id)


@router.get(
    "/categories",
    response_model=List[CategoryRead],
    summary="Получить список категорий"
)
async def get_categories(
        limit: int = Query(100, ge=1, le=500),
        skip: int = Query(0, ge=0),
        service: CategoryService = Depends(get_category_service)
) -> List[CategoryRead]:
    return await service.get_all_categories(limit, skip)


@router.get(
    "/categories/{category_id}",
    response_model=CategoryRead,
    summary="Получить информацию о категории"
)
async def get_category(
        category_id: UUID,
        service: CategoryService = Depends(get_category_service)
) -> CategoryRead:
    return await service.get_category(category_id)


@router.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать товар"
)
async def create_product(
        payload: ProductCreate,
        current_user: User = Depends(get_current_user_dep),
        service: ProductService = Depends(get_product_service)
) -> ProductRead:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return await service.create_product(payload)


@router.put(
    "/products/{product_id}",
    response_model=ProductRead,
    summary="Обновить товар"
)
async def update_product(
        product_id: UUID,
        payload: ProductUpdate,
        current_user: User = Depends(get_current_user_dep),
        service: ProductService = Depends(get_product_service)
) -> ProductRead:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return await service.update_product(product_id, payload)


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить товар"
)
async def delete_product(
        product_id: UUID,
        current_user: User = Depends(get_current_user_dep),
        service: ProductService = Depends(get_product_service)
) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    await service.delete_product(product_id)


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать категорию"
)
async def create_category(
        payload: CategoryCreate,
        current_user: User = Depends(get_current_user_dep),
        service: CategoryService = Depends(get_category_service)
) -> CategoryRead:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return await service.create_category(payload)


@router.put(
    "/categories/{category_id}",
    response_model=CategoryRead,
    summary="Обновить категорию"
)
async def update_category(
        category_id: UUID,
        payload: CategoryUpdate,
        current_user: User = Depends(get_current_user_dep),
        service: CategoryService = Depends(get_category_service)
) -> CategoryRead:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return await service.update_category(category_id, payload)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить категорию"
)
async def delete_category(
        category_id: UUID,
        current_user: User = Depends(get_current_user_dep),
        service: CategoryService = Depends(get_category_service)
) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    await service.delete_category(category_id)