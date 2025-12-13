# app/main.py

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.users.api import router as users_router
from app.auth.api import router as auth_router
from app.cart.api import router as cart_router
from app.catalog.api import router as catalog_router


app = FastAPI(
    title=settings.app.app_name,      
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(cart_router, prefix="/api/v1/cart", tags=["cart"])
app.include_router(catalog_router, prefix="/api/v1/catalog", tags=["catalog"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
