from typing import Any
from sqlalchemy import Column, ForeignKey, Float, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base, BaseModelMixin


class Review(Base, BaseModelMixin):
    __tablename__ = "reviews"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_1_to_5'),
    )

    # Отношения
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "product_id": str(self.product_id),
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }