from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
from datetime import datetime, timedelta, timezone
import json

from app.routers import restaurants, menu, cart, orders
from app.routers import config as config_router
from app.logging_config import setup_logging, get_logger
from app.routers import admin as admin_router
from app.routers import users as users_router
from app.routers import reviews as reviews_router
from app.routers import ra as ra_router
from app.routers import ra_menu as ra_menu_router
from app.routers import auth as auth_router
from app.routers import selections as selections_router
from app.routers import collections as collections_router
from app.routers import public as public_router
from app.db_init import init_db_and_seed

setup_logging()
logger = get_logger("main")
app = FastAPI(title="Yandex Eda TG MiniApp API", version="0.1.0")

# Middleware для увеличения лимита размера файлов
class LargeFileMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Увеличиваем лимит до 50MB для загрузки файлов
        if request.url.path.startswith("/api/admin/broadcast-with-media"):
            # Устанавливаем максимальный размер тела запроса
            request._body = await request.body()
        return await call_next(request)

# Добавляем gzip сжатие для всех ответов больше 1000 байт
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(LargeFileMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники для локальных туннелей
    allow_credentials=False,  # Отключаем credentials для совместимости с allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root_index() -> str:
    logger.info("healthcheck")
    return "<html><body><h3>API is running</h3></body></html>"


app.include_router(restaurants.router, prefix="/api/restaurants", tags=["restaurants"])
app.include_router(menu.router, prefix="/api", tags=["menu"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(config_router.router, prefix="/api", tags=["config"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])
app.include_router(users_router.router, prefix="/api", tags=["users"])
app.include_router(reviews_router.router, prefix="/api", tags=["reviews"])
app.include_router(ra_router.router, prefix="/api", tags=["ra"])
app.include_router(ra_menu_router.router, prefix="/api", tags=["ra-menu"])
app.include_router(selections_router.router, prefix="/api", tags=["selections"])
app.include_router(auth_router.router, prefix="/api", tags=["auth"])
app.include_router(collections_router.router, prefix="/api/collections", tags=["collections"])
app.include_router(public_router.router, prefix="/api/public", tags=["public"])

# static for mini app prototype (built later)
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

# static for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from app.db import get_session
from app.models import Order as DBOrder


async def _delivery_watchdog():
    while True:
        # Используем московское время
        moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(moscow_tz)
        try:
            with get_session() as db:
                rows = db.query(DBOrder).filter(DBOrder.status == "accepted").all()
                changed = False
                for o in rows:
                    if o.accepted_at and o.eta_minutes:
                        # Добавляем минимальное время 5 минут, чтобы избежать мгновенного изменения статуса
                        min_delivery_time = max(o.eta_minutes, 5)
                        if now >= o.accepted_at + timedelta(minutes=min_delivery_time):
                            o.status = "delivered"
                            changed = True
                            logger.info(f"Order {o.id} automatically marked as delivered after {min_delivery_time} minutes")
                if changed:
                    db.commit()
        except Exception:
            pass
        await asyncio.sleep(10)


@app.on_event("startup")
async def _start_watchdog():
    # init DB and seed defaults (idempotent)
    try:
        init_db_and_seed()
    except Exception as exc:
        logger.exception("db init failed: %s", repr(exc))
    asyncio.create_task(_delivery_watchdog())
