from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status
from decimal import Decimal

from app.cart.repository import CartRepository, get_cart_repository
from app.cart.schemas import (
    CartRead, CartItemCreate, CartItemUpdate, CartItemRead
)
from app.cart.enum import CartEnum
from app.catalog.repository import ProductRepository, get_product_repository


class CartService:
    def __init__(self, repo: CartRepository, product_repo: ProductRepository
    ):
        self.repo = repo
        self.product_repo = product_repo

    async def get_or_create_cart(self, user_id: UUID) -> CartRead:
        cart = await self.repo.get_active_cart_by_user(user_id)

        if not cart:
            cart = await self.repo.create_cart(user_id)

        return CartRead.model_validate(cart)

    async def get_cart(self, cart_id: UUID, user_id: UUID) -> CartRead:
        cart = await self.repo.get_cart_by_id(cart_id)

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        if cart.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your cart"
            )

        return CartRead.model_validate(cart)

    async def add_item_to_cart(
            self,
            user_id: UUID,
            item_data: CartItemCreate
    ) -> CartItemRead:
        cart = await self.repo.get_active_cart_by_user(user_id)
        if not cart:
            cart = await self.repo.create_cart(user_id)

        product = await self.product_repo.get_product_by_id(item_data.product_id)
        cart_item = await self.repo.add_item_to_cart(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price_at_add=Decimal(str(product.price))
        )

        return CartItemRead.model_validate(cart_item)

    # изменить количество товара
    async def update_cart_item(
            self,
            user_id: UUID,
            product_id: UUID,
            item_data: CartItemUpdate
    ) -> Optional[CartItemRead]:
        cart = await self.repo.get_active_cart_by_user(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        updated_item = await self.repo.update_item_quantity(
            cart_id=cart.id,
            product_id=product_id,
            quantity=item_data.quantity
        )

        if updated_item:
            return CartItemRead.model_validate(updated_item)
        return None

    async def remove_item_from_cart(
            self,
            user_id: UUID,
            product_id: UUID
    ) -> bool:
        cart = await self.repo.get_active_cart_by_user(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        return await self.repo.remove_item_from_cart(cart.id, product_id)

    async def clear_cart(self, user_id: UUID) -> bool:
        cart = await self.repo.get_active_cart_by_user(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        await self.repo.clear_cart(cart.id)
        return True

    async def checkout_cart(self, user_id: UUID) -> CartRead:
        cart = await self.repo.get_active_cart_by_user(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )

        updated_cart = await self.repo.update_cart_status(
            cart_id=cart.id,
            status=CartEnum.ORDERED
        )

        return CartRead.model_validate(updated_cart)


async def get_cart_service(
    repo: CartRepository = Depends(get_cart_repository),
    product_repo: ProductRepository = Depends(get_product_repository)  # ← Исправляем
) -> CartService:
    return CartService(repo, product_repo)
