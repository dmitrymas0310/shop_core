from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.cart.service import CartService, get_cart_service
from app.cart.schemas import CartItemCreate, CartItemUpdate, CartItemRead, CartRead
from app.auth.service import get_current_user_dep
from app.users.models import User
from app.users.enum import UserRole

router = APIRouter(
    prefix="/cart",
    tags=["cart"],
)


@router.get(
    "/",
    response_model=CartRead,
    summary="Получить свою корзину"
)
async def get_my_cart(
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> CartRead:
    return await service.get_or_create_cart(current_user.id)


@router.get(
    "/items",
    response_model=List[CartItemRead],
    summary="Получить товары в своей корзине"
)
async def get_cart_items(
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> List[CartItemRead]:
    cart = await service.get_or_create_cart(current_user.id)
    return cart.items


@router.post(
    "/items",
    response_model=CartItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить товар в свою корзину"
)
async def add_item_to_cart(
        payload: CartItemCreate,
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> CartItemRead:
    return await service.add_item_to_cart(current_user.id, payload)


@router.delete(
    "/clear",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Очистить свою корзину"
)
async def clear_cart(
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> None:
    await service.clear_cart(current_user.id)


@router.post(
    "/checkout",
    response_model=CartRead,
    summary="Оформить заказ из своей корзины"
)
async def checkout_cart(
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> CartRead:
    return await service.checkout_cart(current_user.id)


@router.put(
    "/items/{product_id}",
    response_model=CartItemRead,
    summary="Изменить количество товара в своей корзине"
)
async def update_cart_item(
        product_id: UUID,
        payload: CartItemUpdate,
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> CartItemRead:
    updated_item = await service.update_cart_item(
        current_user.id, product_id, payload
    )

    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    return updated_item


@router.get(
    "/{user_id}",
    response_model=CartRead,
    summary="Получить корзину пользователя"
)
async def get_user_cart(
        user_id: UUID,
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> CartRead:
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return await service.get_or_create_cart(user_id)


@router.delete(
    "/items/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить товар из своей корзины"
)
async def remove_item_from_cart(
        product_id: UUID,
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> None:
    success = await service.remove_item_from_cart(current_user.id, product_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )


@router.delete(
    "/{user_id}/clear",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Очистить корзину пользователя (админ)"
)
async def clear_user_cart(
        user_id: UUID,
        current_user: User = Depends(get_current_user_dep),
        service: CartService = Depends(get_cart_service)
) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    await service.clear_cart(user_id)