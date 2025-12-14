
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base  
from sqlalchemy.dialects.postgresql import UUID

class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    product_id = Column(UUID, ForeignKey("products.id"), nullable=False)  
    rating = Column(Float, nullable=False)  
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Отношения
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews") 