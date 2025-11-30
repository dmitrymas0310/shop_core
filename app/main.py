# app/main.py

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.users.api import router as users_router


app = FastAPI(
    title="Shop-core",      
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(users_router, prefix="/api/v1/users", tags=["users"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
