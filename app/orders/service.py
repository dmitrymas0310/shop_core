from uuid import UUID
from typing import List, Optional
from fastapi import Depends, HTTPException, status

from app.orders.repository import OrderRepository, get_order_repository
from app.orders.schemas import OrderCreate, OrderRead, OrderUpdate, OrderStatusUpdate, OrderStatusEnum
from app.orders.models import OrderStatus
from app.catalog.repository import ProductRepository, get_product_repository
from app.cart.service import CartService, get_cart_service
from app.users.repository import UserRepository, get_user_repository


class OrderService:
	def __init__(self, order_repo: OrderRepository, product_repo: ProductRepository,
				 user_repo: UserRepository, cart_service: CartService):
		self.order_repo = order_repo
		self.product_repo = product_repo
		self.user_repo = user_repo
		self.cart_service = cart_service

	async def create_order_from_cart(self, user_id: UUID, order_data: OrderCreate) -> OrderRead:
		user = await self.user_repo.get_by_id(user_id)
		if not user:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="User not found"
			)

		order = await self.order_repo.create_order(
			user_id=user_id,
			shipping_address=order_data.shipping_address,
			phone_number=order_data.phone_number,
			notes=order_data.notes
		)

		total_amount = 0.0

		for item in order_data.items:
			product = await self.product_repo.get_by_id(item.product_id)
			if not product:
				await self.order_repo.delete_order(order.id)
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail=f"Product with id {item.product_id} not found"
				)

			if hasattr(product, 'stock_quantity') and product.stock_quantity < item.quantity:
				await self.order_repo.delete_order(order.id)
				raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail=f"Not enough stock for product {product.name}. Available: {product.stock_quantity}"
				)

			await self.order_repo.add_order_item(
				order_id=order.id,
				product_id=product.id,
				quantity=item.quantity,
				price=product.price,
				product_name=product.name
			)

			if hasattr(product, 'stock_quantity'):
				await self.product_repo.update_product(
					product.id, 
					{"stock_quantity": product.stock_quantity - item.quantity}
				)

			total_amount += item.quantity * product.price

		await self.order_repo.update_order_total(order.id, total_amount)

		full_order = await self.order_repo.get_order_by_id(order.id)
		return OrderRead.model_validate(full_order)

	async def get_user_order(self, user_id: UUID, order_id: UUID) -> OrderRead:
		order = await self.order_repo.get_user_order(user_id, order_id)
		if not order:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Order not found"
			)
		return OrderRead.model_validate(order)

	async def get_user_orders(self, user_id: UUID, limit: int = 100, 
							 skip: int = 0) -> List[OrderRead]:
		orders = await self.order_repo.get_user_orders(user_id, limit, skip)
		return [OrderRead.model_validate(order) for order in orders]

	async def get_all_orders(self, limit: int = 100, skip: int = 0,
							status: Optional[OrderStatusEnum] = None) -> List[OrderRead]:
		order_status = None
		if status:
			order_status = OrderStatus(status.value)

		orders = await self.order_repo.get_all_orders(limit, skip, order_status)
		return [OrderRead.model_validate(order) for order in orders]

	async def update_order_status(self, order_id: UUID, status_update: OrderStatusUpdate,
								 current_user_id: UUID) -> OrderRead:
		order = await self.order_repo.get_order_by_id(order_id)
		if not order:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Order not found"
			)

		user = await self.user_repo.get_by_id(current_user_id)

		can_update = False

		if user.role == "admin":
			can_update = True
		elif order.user_id == current_user_id:
			if status_update.status == OrderStatusEnum.CANCELLED and order.status == OrderStatus.PENDING:
				can_update = True

		if not can_update:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Not enough permissions to update order status"
			)

		updated_order = await self.order_repo.update_order_status(
			order_id, 
			OrderStatus(status_update.status.value)
		)

		return OrderRead.model_validate(updated_order)

	async def update_order(self, order_id: UUID, update_data: OrderUpdate,
						  current_user_id: UUID) -> OrderRead:
		order = await self.order_repo.get_order_by_id(order_id)
		if not order:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="Order not found"
			)

		user = await self.user_repo.get_by_id(current_user_id)
		if user.role != "admin" and order.user_id != current_user_id:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Not enough permissions to update this order"
			)

		update_dict = update_data.model_dump(exclude_unset=True)

		updated_order = await self.order_repo.update_order(order_id, update_dict)
		return OrderRead.model_validate(updated_order)


async def get_order_service(
	order_repo: OrderRepository = Depends(get_order_repository),
	product_repo: ProductRepository = Depends(get_product_repository),
	user_repo: UserRepository = Depends(get_user_repository),
	cart_service: CartService = Depends(get_cart_service),
) -> OrderService:
	return OrderService(order_repo, product_repo, user_repo, cart_service)