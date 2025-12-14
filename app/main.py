# app/main.py

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.users.api import router as users_router
from app.auth.api import router as auth_router
from app.cart.api import router as cart_router
from app.catalog.api import router as catalog_router
from app.promotions.api import router as promotions_router
from app.reviews.router import router as reviews_router
from app.orders.api import router as orders_router

app = FastAPI(
    title=settings.app.app_name,      
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(reviews_router)

app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(cart_router, prefix="/api/v1/cart", tags=["cart"])
app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["catalog"])
app.include_router(promotions_router, prefix="/api/v1/promotions", tags=["promotions"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["orders"])



if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
