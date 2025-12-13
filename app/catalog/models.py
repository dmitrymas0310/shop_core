from typing import Any
from decimal import Decimal
from sqlalchemy import Column, String, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.db import Base, BaseModelMixin
from app.users.enum import UserRole
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Integer, Float, Numeric, CheckConstraint


class Category(Base, BaseModelMixin):
    __tablename__ = "categories"

    name = Column(String, nullable=False)
    products = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name={self.name})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "products_count": len(self.products) if self.products else 0
        }


class Product(Base, BaseModelMixin):
    __tablename__ = "products"

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(
        Numeric(10, 2),
        nullable=False
    )
    rating = Column(
        Float,
        nullable=True,
        default=None,
        comment="Рейтинг товара от 0 до 5"
    )
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )

    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('rating >= 0 AND rating <= 5', name='check_rating_range'),
    )
    category = relationship("Category", back_populates="products", lazy="selectin")

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name}, price={self.price}, rating={self.rating})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price else None,
            "rating": self.rating,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
        }
