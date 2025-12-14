from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.cart.enum import CartEnum

# cart item
class CartItemCreate(BaseModel):
    product_id: UUID
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemRead(BaseModel):
    id: UUID
    cart_id: UUID
    product_id: UUID
    quantity: int
    price_at_add: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# cart
class CartRead(BaseModel):
    id: UUID
    user_id: UUID
    status: CartEnum
    items: List[CartItemRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True