from typing import Any
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base, BaseModelMixin


class Promotion(Base, BaseModelMixin):
    __tablename__ = "promotions"

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    discount_percent = Column(Float, nullable=False, comment="Процент скидки (0-100)")
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Связь many-to-many через PromotionProduct
    promotion_products = relationship(
        "PromotionProduct",
        back_populates="promotion",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"Promotion(id={self.id}, title={self.title}, discount={self.discount_percent}%)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "discount_percent": self.discount_percent,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class PromotionProduct(Base):
    __tablename__ = "promotion_products"

    promotion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("promotions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )

    # Relationships
    promotion = relationship("Promotion", back_populates="promotion_products")
    product = relationship("Product", lazy="selectin")

    def __repr__(self) -> str:
        return f"PromotionProduct(promotion_id={self.promotion_id}, product_id={self.product_id})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "promotion_id": self.promotion_id,
            "product_id": self.product_id
        }
