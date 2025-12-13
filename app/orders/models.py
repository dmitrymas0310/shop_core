from typing import Optional, Any
from sqlalchemy import Column, String, Float, Integer, Enum as SAEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from app.core.db import Base, BaseModelMixin

class OrderStatus(str, Enum):
	PENDING = "pending"
	PROCESSING = "processing"
	SHIPPED = "shipped"
	DELIVERED = "delivered"
	CANCELLED = "cancelled"

class Order(Base, BaseModelMixin):
	__tablename__ = "orders"

	user_id = Column(ForeignKey("users.id"), nullable=False)
	status = Column(SAEnum(OrderStatus, name="order_status_enum"), 
					nullable=False, default=OrderStatus.PENDING)
	total_amount = Column(Float, nullable=False, default=0.0)
	shipping_address = Column(String, nullable=False)
	phone_number = Column(String, nullable=False)
	notes = Column(String, nullable=True)
	ordered_at = Column(DateTime(timezone=True), server_default=func.now())

	user = relationship("User", backref="orders", lazy="select")
	items = relationship("OrderItem", back_populates="order", 
						cascade="all, delete-orphan", lazy="select")

	def __repr__(self) -> str:
		return f"Order(id={self.id}, user_id={self.user_id}, status={self.status}, total={self.total_amount})"

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"user_id": self.user_id,
			"status": self.status,
			"total_amount": self.total_amount,
			"shipping_address": self.shipping_address,
			"phone_number": self.phone_number,
			"notes": self.notes,
			"ordered_at": self.ordered_at.isoformat() if self.ordered_at else None,
			"created_at": self.created_at.isoformat() if self.created_at else None,
			"updated_at": self.updated_at.isoformat() if self.updated_at else None,
		}

class OrderItem(Base, BaseModelMixin):
	__tablename__ = "order_items"

	order_id = Column(ForeignKey("orders.id"), nullable=False)
	product_id = Column(ForeignKey("products.id"), nullable=False)
	quantity = Column(Integer, nullable=False, default=1)
	price_at_time = Column(Float, nullable=False)  # Цена на момент заказа
	product_name = Column(String, nullable=False)  # Название на момент заказа

	order = relationship("Order", back_populates="items")
	product = relationship("Product", backref="order_items")

	def __repr__(self) -> str:
		return f"OrderItem(id={self.id}, order_id={self.order_id}, product={self.product_name}, qty={self.quantity})"

	def to_dict(self) -> dict[str, Any]:
		return {
			"id": self.id,
			"order_id": self.order_id,
			"product_id": self.product_id,
			"product_name": self.product_name,
			"quantity": self.quantity,
			"price_at_time": self.price_at_time,
			"subtotal": self.quantity * self.price_at_time,
		}