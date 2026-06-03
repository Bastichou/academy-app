from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.health import router as health_router
from .routes.messages import router as messages_router
from .routes.config import router as config_router
from .routes.redis_kv import router as redis_kv_router

app = FastAPI(title="Academy Cloud API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(redis_kv_router, prefix="/api")
