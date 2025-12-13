from typing import Any
from decimal import Decimal
from sqlalchemy import Column, String, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.db import Base, BaseModelMixin
from app.cart.enum import CartEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Integer, Numeric


class Cart(Base, BaseModelMixin):
    __tablename__ = "carts"

    user_id = Column(UUID(as_uuid=True),
                     ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False)
    status = Column(SAEnum(CartEnum,
                           name="cart_status_enum"),
                    nullable=False,
                    default=CartEnum.ACTIVE)

    user = relationship("User", back_populates="carts", lazy="selectin")
    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Cart(id={self.id}, user_id={self.user_id}, status={self.status}, items_count={len(self.items) if self.items else 0})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status.value if isinstance(self.status, CartEnum) else self.status,
            "items": [item.to_dict() for item in self.items] if self.items else []
        }

    def calculate_total_price(self) -> Decimal:
        if not self.items:
            return Decimal('0.00')
        return sum(item.calculate_total() for item in self.items)


class CartItem(Base, BaseModelMixin):
    __tablename__ = "cart_items"

    cart_id = Column(
        UUID(as_uuid=True),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity = Column(Integer, nullable=False, default=1)
    price_at_add = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Цена товара на момент добавления в корзину"
    )

    cart = relationship("Cart", back_populates="items", lazy="selectin")
    product = relationship("Product", lazy="selectin", primaryjoin="CartItem.product_id == Product.id")

    def __repr__(self) -> str:
        return f"CartItem(id={self.id}, cart_id={self.cart_id}, product_id={self.product_id}, quantity={self.quantity}, price={self.price_at_add})"

    def to_dict(self) -> dict[str, Any]:
        product_data = self.product.to_dict() if hasattr(self.product, 'to_dict') else {"id": self.product_id}
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price_at_add": float(self.price_at_add) if self.price_at_add else None,
            "total_price": float(self.calculate_total()),
            "product": product_data
        }

    def calculate_total(self) -> Decimal:
        if self.price_at_add and self.quantity:
            return Decimal(str(self.price_at_add)) * Decimal(str(self.quantity))
        return Decimal('0.00')
