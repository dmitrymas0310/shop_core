from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PromotionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    discount_percent: float = Field(..., ge=0, le=100)
    starts_at: datetime
    ends_at: datetime
    is_active: bool = True


class PromotionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class PromotionRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    discount_percent: float
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromotionWithProducts(PromotionRead):
    product_ids: List[UUID] = []

    class Config:
        from_attributes = True


class AttachProductsRequest(BaseModel):
    product_ids: List[UUID] = Field(..., min_items=1)


class PromotionProductRead(BaseModel):
    promotion_id: UUID
    product_id: UUID

    class Config:
        from_attributes = True
