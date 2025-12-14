from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# catalog
class CategoryCreate(BaseModel):
    name: str

class CategoryUpdate(BaseModel):
    name: str

class CategoryRead(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# product

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    rating: Optional[float] = None
    category_id: Optional[UUID] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    rating: Optional[float] = None
    category_id: Optional[UUID] = None

class ProductRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    price: Decimal
    rating: Optional[float]
    category_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True