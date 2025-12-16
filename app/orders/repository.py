from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import Depends
from app.orders.models import Order, OrderItem, OrderStatus
from app.catalog.models import Product
from app.core.db import get_session

class OrderRepository:
	def __init__(self, db):
		self.db = db

	async def create_order(self, user_id: UUID, shipping_address: str, 
						  phone_number: str, notes: Optional[str] = None) -> Order:
		order = Order(
			user_id=user_id,
			shipping_address=shipping_address,
			phone_number=phone_number,
			notes=notes
		)
		self.db.add(order)
		await self.db.commit()
		await self.db.refresh(order)
		return order

	async def add_order_item(self, order_id: UUID, product_id: UUID, 
							quantity: int, price: float, product_name: str) -> OrderItem:
		item = OrderItem(
			order_id=order_id,
			product_id=product_id,
			quantity=quantity,
			price_at_time=price,
			product_name=product_name
		)
		self.db.add(item)
		await self.db.commit()
		await self.db.refresh(item)
		return item

	async def get_order_by_id(self, order_id: UUID) -> Optional[Order]:
		query = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
		result = await self.db.execute(query)
		return result.scalar_one_or_none()

	async def get_user_order(self, user_id: UUID, order_id: UUID) -> Optional[Order]:
		query = select(Order).options(selectinload(Order.items)).where(
			and_(Order.id == order_id, Order.user_id == user_id)
		)
		result = await self.db.execute(query)
		return result.scalar_one_or_none()

	async def get_user_orders(self, user_id: UUID, limit: int = 100, 
							 skip: int = 0) -> List[Order]:
		query = (select(Order)
				 .options(selectinload(Order.items))
				 .where(Order.user_id == user_id)
				 .order_by(Order.created_at.desc())
				 .offset(skip)
				 .limit(limit))
		result = await self.db.execute(query)
		return result.scalars().all()

	async def get_all_orders(self, limit: int = 100, skip: int = 0,
							status: Optional[OrderStatus] = None) -> List[Order]:
		query = select(Order).options(selectinload(Order.items))

		if status:
			query = query.where(Order.status == status)

		query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
		result = await self.db.execute(query)
		return result.scalars().all()

	async def update_order(self, order_id: UUID, update_data: dict) -> Optional[Order]:
		if not update_data:
			return await self.get_order_by_id(order_id)

		# Обновляем заказ
		stmt = update(Order).where(Order.id == order_id).values(**update_data).returning(Order)
		result = await self.db.execute(stmt)
		await self.db.commit()

		order = result.scalar_one_or_none()
		if order:
			await self.db.refresh(order)
		return order

	async def update_order_status(self, order_id: UUID, status: OrderStatus) -> Optional[Order]:
		stmt = update(Order).where(Order.id == order_id).values(status=status).returning(Order)
		result = await self.db.execute(stmt)
		await self.db.commit()

		order = result.scalar_one_or_none()
		if order:
			await self.db.refresh(order)
		return order

	async def update_order_total(self, order_id: UUID, total_amount: float) -> None:
		stmt = update(Order).where(Order.id == order_id).values(total_amount=total_amount)
		await self.db.execute(stmt)
		await self.db.commit()

	async def delete_order(self, order_id: UUID) -> bool:
		stmt = delete(Order).where(Order.id == order_id)
		result = await self.db.execute(stmt)
		await self.db.commit()
		return result.rowcount > 0

	async def get_order_items_total(self, order_id: UUID) -> float:
		query = select(OrderItem).where(OrderItem.order_id == order_id)
		result = await self.db.execute(query)
		items = result.scalars().all()

		total = sum(item.quantity * item.price_at_time for item in items)
		return total

	async def get_orders_count(self, user_id: Optional[UUID] = None) -> int:
		query = select(Order)
		if user_id:
			query = query.where(Order.user_id == user_id)

		result = await self.db.execute(query)
		return len(result.scalars().all())


async def get_order_repository(db: AsyncSession = Depends(get_session)) -> OrderRepository:
	return OrderRepository(db)
