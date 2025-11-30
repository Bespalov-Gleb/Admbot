from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.db import get_session
from app.models import User as DBUser, RestaurantAdmin as DBRestaurantAdmin


def ensure_user(user_id: int, username: str | None = None) -> DBUser:
    with get_session() as db:  # type: Session
        u = db.query(DBUser).filter(DBUser.id == user_id).first()
        if not u:
            u = DBUser(id=user_id, is_blocked=False, created_at=datetime.utcnow(), last_activity=datetime.utcnow(), username=username)
            db.add(u)
            db.commit()
        else:
            # Обновляем last_activity и username для существующих пользователей
            u.last_activity = datetime.utcnow()
            if username and not u.username:
                u.username = username
            db.commit()
        return u


def bind_restaurant_admin(user_id: int, restaurant_id: int) -> None:
    """Добавляет пользователя как админа ресторана. Поддерживает несколько ресторанов для одного пользователя."""
    print(f"DEBUG: bind_restaurant_admin called with user_id={user_id}, restaurant_id={restaurant_id}")
    with get_session() as db:
        # Сначала убеждаемся, что пользователь существует
        ensure_user(user_id)
        print(f"DEBUG: user {user_id} ensured")
        
        # Проверяем, существует ли уже такая связь
        row = db.query(DBRestaurantAdmin).filter(
            DBRestaurantAdmin.user_id == user_id,
            DBRestaurantAdmin.restaurant_id == restaurant_id
        ).first()
        
        if row:
            print(f"DEBUG: admin record already exists for user {user_id} and restaurant {restaurant_id}")
        else:
            print(f"DEBUG: creating new admin record for user {user_id} and restaurant {restaurant_id}")
            db.add(DBRestaurantAdmin(user_id=user_id, restaurant_id=restaurant_id))
            db.commit()
            print(f"DEBUG: commit successful")


def unbind_restaurant_admin(user_id: int, restaurant_id: int | None = None) -> None:
    """Удаляет связь пользователя с рестораном. Если restaurant_id не указан, удаляет все связи пользователя."""
    with get_session() as db:
        if restaurant_id is not None:
            # Удаляем конкретную связь
            row = db.query(DBRestaurantAdmin).filter(
                DBRestaurantAdmin.user_id == user_id,
                DBRestaurantAdmin.restaurant_id == restaurant_id
            ).first()
            if row:
                db.delete(row)
                db.commit()
        else:
            # Удаляем все связи пользователя (старое поведение для обратной совместимости)
            rows = db.query(DBRestaurantAdmin).filter(DBRestaurantAdmin.user_id == user_id).all()
            for row in rows:
                db.delete(row)
            db.commit()


def get_restaurants_for_admin(user_id: int) -> List[int]:
    """Возвращает список ID ресторанов, для которых пользователь является админом."""
    with get_session() as db:
        rows = db.query(DBRestaurantAdmin).filter(DBRestaurantAdmin.user_id == user_id).all()
        return [row.restaurant_id for row in rows]


def get_restaurant_for_admin(user_id: int) -> int | None:
    """Возвращает первый ресторан пользователя (для обратной совместимости)."""
    restaurants = get_restaurants_for_admin(user_id)
    return restaurants[0] if restaurants else None


def get_user_by_username(username: str) -> int | None:
    """Находит пользователя по username в базе данных"""
    clean_username = username.lstrip('@')
    with get_session() as db:
        user = db.query(DBUser).filter(DBUser.username == clean_username).first()
        return user.id if user else None


# Временные заглушки для совместимости с существующим кодом, где импортируются эти имена
users: Dict[int, Any] = {}
ORDERS: List[Any] = []
ORDER_SEQ: int = 1
REVIEWS: List[Any] = []
REV_SEQ: int = 1

