from uuid import UUID
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from app.orders.models import OrderStatus

class OrderStatusEnum(str, Enum):
	PENDING = "pending"
	PROCESSING = "processing"
	SHIPPED = "shipped"
	DELIVERED = "delivered"
	CANCELLED = "cancelled"

class OrderItemCreate(BaseModel):
	product_id: UUID
	quantity: int = Field(ge=1, le=100)

	@validator('quantity')
	def validate_quantity(cls, v):
		if v <= 0:
			raise ValueError('Quantity must be positive')
		return v

class OrderCreate(BaseModel):
	shipping_address: str = Field(..., min_length=5, max_length=500)
	phone_number: str = Field(..., min_length=5, max_length=20)
	notes: Optional[str] = Field(None, max_length=1000)
	items: List[OrderItemCreate] = Field(..., min_items=1)


class OrderUpdate(BaseModel):
	status: Optional[OrderStatusEnum] = None
	shipping_address: Optional[str] = Field(None, min_length=5, max_length=500)
	phone_number: Optional[str] = Field(None, min_length=5, max_length=20)
	notes: Optional[str] = Field(None, max_length=1000)

class OrderItemRead(BaseModel):
	id: UUID
	product_id: UUID
	product_name: str
	quantity: int
	price_at_time: float
	subtotal: float

	class Config:
		from_attributes = True

class OrderRead(BaseModel):
	id: UUID
	user_id: UUID
	status: OrderStatusEnum
	total_amount: float
	shipping_address: str
	phone_number: str
	notes: Optional[str]
	ordered_at: datetime
	items: List[OrderItemRead]
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True

class OrderStatusUpdate(BaseModel):
	status: OrderStatusEnum