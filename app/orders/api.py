from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.orders.service import OrderService, get_order_service
from app.orders.schemas import OrderCreate, OrderRead, OrderUpdate, OrderStatusUpdate, OrderStatusEnum
from app.auth.service import get_current_user_dep, require_admin
from app.users.models import User

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)

@router.post(
    "/",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый заказ из корзины",
)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user_dep),
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    """
    Создать новый заказ из текущей корзины пользователя.
    """
    return await service.create_order_from_cart(current_user.id, order_data)

@router.get(
    "/my",
    response_model=List[OrderRead],
    summary="Получить список моих заказов",
)
async def get_my_orders(
    limit: int = Query(100, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_dep),
    service: OrderService = Depends(get_order_service),
) -> List[OrderRead]:
    """
    Получить список заказов текущего пользователя.
    """
    return await service.get_user_orders(current_user.id, limit, skip)

@router.get(
    "/my/{order_id}",
    response_model=OrderRead,
    summary="Получить мой заказ по ID",
)
async def get_my_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user_dep),
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    """
    Получить конкретный заказ текущего пользователя.
    """
    return await service.get_user_order(current_user.id, order_id)

@router.get(
    "/",
    response_model=List[OrderRead],
    summary="Получить список всех заказов",
)
async def get_all_orders(
    limit: int = Query(100, ge=1, le=200),
    skip: int = Query(0, ge=0),
    status: Optional[OrderStatusEnum] = Query(None),
    admin: User = Depends(require_admin),
    service: OrderService = Depends(get_order_service),
) -> List[OrderRead]:
    """
    Получить список всех заказов в системе.
    """
    return await service.get_all_orders(limit, skip, status)

@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Обновить статус заказа",
)
async def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_current_user_dep),
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    """
    Обновить статус заказа.
    Администраторы могут обновлять любой статус.
    Пользователи могут отменять только свои заказы со статусом 'pending'.
    """
    return await service.update_order_status(order_id, status_update, current_user.id)

@router.patch(
    "/{order_id}",
    response_model=OrderRead,
    summary="Обновить данные заказа",
)
async def update_order(
    order_id: UUID,
    order_update: OrderUpdate,
    current_user: User = Depends(get_current_user_dep),
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    """
    Обновить информацию о заказе.
    Администраторы могут обновлять любые заказы.
    Пользователи могут обновлять только свои заказы.
    """
    return await service.update_order(order_id, order_update, current_user.id)

@router.get(
    "/stats/count",
    summary="Получить статистику по заказам",
)
async def get_orders_stats(
    admin: User = Depends(require_admin),
    service: OrderService = Depends(get_order_service),
    user_id: Optional[UUID] = Query(None, description="ID пользователя для фильтрации"),
) -> dict:
    """
    Получить количество заказов.
    Если передан user_id - только заказы этого пользователя.
    """
    count = await service.order_repo.get_orders_count(user_id)
    return {
        "count": count,
        "user_id": user_id,
        "message": "Статистика по заказам"
    }
@router.get(
    "/stats/summary",
    summary="Получить сводную статистику",
)
async def get_orders_summary(
    admin: User = Depends(require_admin),
    service: OrderService = Depends(get_order_service),
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа"),
) -> dict:
    """
    Получить сводную статистику по заказам.
    """
    # Здесь логика для получения расширенной статистики
    # общая выручка, средний чек, популярные товары и т.д.
    return {
        "period_days": days,
        "total_orders": 0,
        "total_revenue": 0.0,
        "avg_order_value": 0.0,
        "most_ordered_products": []
    }

@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить заказ",
)
async def delete_order(
    order_id: UUID,
    admin: User = Depends(require_admin),
    service: OrderService = Depends(get_order_service),
) -> None:
    """
    Удалить заказ из системы.
    Внимание: удаление возможно только для заказов со статусом 'cancelled'.
    """
    # Проверяем, существует ли заказ
    order = await service.order_repo.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    # Можно удалять только отмененные заказы
    if order.status != "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only cancelled orders can be deleted"
        )
    await service.order_repo.delete_order(order_id) 
