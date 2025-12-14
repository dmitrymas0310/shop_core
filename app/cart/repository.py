from uuid import UUID
from decimal import Decimal
from typing import Optional, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.orm import selectinload

from app.core.db import get_session
from app.cart.models import Cart, CartItem
from app.cart.enum import CartEnum
from app.catalog.models import Product


class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_cart(self, user_id: UUID) -> Cart:
        cart = Cart(
            user_id=user_id,
            status=CartEnum.ACTIVE)
        self.db.add(cart)
        await self.db.commit()
        await self.db.refresh(cart)
        return cart

    async def get_active_cart_by_user(self, user_id: UUID) -> Optional[Cart]:
        result = await self.db.execute(
            select(Cart)
            .options(
                selectinload(Cart.items)
                .selectinload(CartItem.product)
                .selectinload(Product.category)
            )
            .where(
                and_(
                    Cart.user_id == user_id,
                    Cart.status == CartEnum.ACTIVE
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_cart_by_id(self, cart_id: UUID) -> Optional[Cart]:
        result = await self.db.execute(
            select(Cart)
            .options(
                selectinload(Cart.items)
                .selectinload(CartItem.product)
            )
            .where(Cart.id == cart_id)
        )
        return result.scalar_one_or_none()

    async def update_cart_status(self, cart_id: UUID, status: CartEnum) -> Cart:
        query = (
            update(Cart)
            .where(Cart.id == cart_id)
            .values(status=status)
            .returning(Cart)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one()

    async def clear_cart(self, cart_id: UUID) -> None:
        await self.db.execute(
            delete(CartItem).where(CartItem.cart_id == cart_id)
        )
        await self.db.commit()

    # card item methods
    async def add_item_to_cart(
            self,
            cart_id: UUID,
            product_id: UUID,
            quantity: int,
            price_at_add: Decimal
    ) -> CartItem:
        existing_item = await self.get_cart_item(cart_id, product_id)

        if existing_item:
            new_quantity = existing_item.quantity + quantity
            query = (
                update(CartItem)
                .where(
                    and_(
                        CartItem.cart_id == cart_id,
                        CartItem.product_id == product_id
                    )
                )
                .values(quantity=new_quantity)
                .returning(CartItem)
            )
            result = await self.db.execute(query)
            item = result.scalar_one()
        else:
            item = CartItem(
                cart_id=cart_id,
                product_id=product_id,
                quantity=quantity,
                price_at_add=price_at_add
            )
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_cart_item(self, cart_id: UUID, product_id: UUID) -> Optional[CartItem]:
        result = await self.db.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(
                and_(
                    CartItem.cart_id == cart_id,
                    CartItem.product_id == product_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_item_quantity(
            self,
            cart_id: UUID,
            product_id: UUID,
            quantity: int
    ) -> Optional[CartItem]:
        if quantity <= 0:
            await self.remove_item_from_cart(cart_id, product_id)
            return None

        query = (
            update(CartItem)
            .where(
                and_(
                    CartItem.cart_id == cart_id,
                    CartItem.product_id == product_id
                )
            )
            .values(quantity=quantity)
            .returning(CartItem)
        )
        result = await self.db.execute(query)
        await self.db.commit()

        item = result.scalar_one_or_none()  # ← Используем scalar_one_or_none

        if item:
            await self.db.refresh(item)
            return item
        return None

    async def remove_item_from_cart(self, cart_id: UUID, product_id: UUID) -> bool:
        query = delete(CartItem).where(
            and_(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id
            )
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

    async def get_cart_items_count(self, cart_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(CartItem.id))
            .where(CartItem.cart_id == cart_id)
        )
        return result.scalar_one()


async def get_cart_repository(db: AsyncSession = Depends(get_session)) -> CartRepository:
    return CartRepository(db)
