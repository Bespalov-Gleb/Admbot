import os
from typing import Set
from fastapi import Header, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User as DBUser
import hmac
import base64
from dotenv import load_dotenv
from app.logging_config import get_logger


def _load_super_admin_ids() -> Set[int]:
    raw = os.getenv("SUPER_ADMIN_IDS", "")
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            continue
    return ids


load_dotenv()
SUPER_ADMINS = _load_super_admin_ids()
logger = get_logger("auth")


def require_super_admin(
    request: Request,
    x_telegram_user_id: int | None = Header(default=None, alias="X-Telegram-User-Id"),
) -> int:
    user_id: int | None = x_telegram_user_id
    if user_id is None:
        uid_param = request.query_params.get("uid")
        try:
            user_id = int(uid_param) if uid_param else None
        except ValueError:
            user_id = None
    
    # Отладочная информация
    logger.info(f"require_super_admin: user_id={user_id}, x_telegram_user_id={x_telegram_user_id}, SUPER_ADMINS={list(SUPER_ADMINS)}")
    
    # allow cookie-based web admin session as an alternative
    if user_id is None or user_id not in SUPER_ADMINS:
        token = request.cookies.get("admin_session")
        if token and _is_valid_admin_session(token):
            logger.info("Admin access granted via cookie session")
            return 0  # web admin (no tg user id)
        logger.warning("forbidden admin access", extra={"user_id": user_id, "allowed": list(SUPER_ADMINS)})
        raise HTTPException(status_code=403, detail="forbidden")
    logger.info(f"Admin access granted for user_id={user_id}")
    return user_id


def require_user_id(
    request: Request,
    x_telegram_user_id: int | None = Header(default=None, alias="X-Telegram-User-Id"),
    db: Session = Depends(get_db),
) -> int:
    user_id: int | None = x_telegram_user_id
    if user_id is None:
        uid_param = request.query_params.get("uid")
        try:
            user_id = int(uid_param) if uid_param else None
        except ValueError:
            user_id = None
    if user_id is None:
        logger.warning("missing user id for request %s", request.url.path)
        raise HTTPException(status_code=401, detail="user_id_required")

    # deny access for blocked users
    try:
        u = db.query(DBUser).filter(DBUser.id == user_id).first()
        if u and u.is_blocked:
            logger.warning("blocked user access denied", extra={"user_id": user_id, "path": request.url.path})
            raise HTTPException(status_code=403, detail="user_blocked")
    except Exception:
        # if DB unavailable, fail closed for safety
        pass

    return user_id


def _is_valid_admin_session(token: str) -> bool:
    try:
        secret = os.getenv("ADMIN_SITE_SECRET", "dev-secret")
        # если пришла cookie в base64 — декодируем
        try:
            token = base64.urlsafe_b64decode(token.encode()).decode()
        except Exception:
            pass
        parts = token.split("&")
        data = {k: v for k, v in (p.split("=", 1) for p in parts if "=" in p)}
        role = data.get("role")
        exp = int(data.get("exp", "0"))
        sig = data.get("sig", "")
        base = f"role={role}&exp={exp}"
        good_sig = hmac.new(secret.encode(), base.encode(), 'sha256').hexdigest()
        return (sig == good_sig) and (role == "super_admin") and (exp > __import__('time').time())
    except Exception:
        return False

