from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base  # предполагается, что Base определён в core.database

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # или catalog.id
    rating = Column(Float, nullable=False)  # от 1 до 5, например
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Отношения
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")  # или Catalog