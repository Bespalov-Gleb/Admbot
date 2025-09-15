from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.deps.auth import require_user_id
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import Review as DBReview, Order as DBOrder, AppReview as DBAppReview, Restaurant as DBRestaurant, User as DBUser, OrderItem as DBOrderItem


router = APIRouter()


def update_restaurant_rating(restaurant_id: int, db: Session):
    """Обновляет рейтинг ресторана на основе всех отзывов"""
    # Получаем средний рейтинг всех активных отзывов для ресторана
    avg_rating = db.query(func.avg(DBReview.rating)).filter(
        DBReview.restaurant_id == restaurant_id,
        DBReview.is_deleted == False
    ).scalar()
    
    # Обновляем рейтинг ресторана
    restaurant = db.query(DBRestaurant).filter(DBRestaurant.id == restaurant_id).first()
    if restaurant:
        restaurant.rating_agg = round(avg_rating or 0.0, 1)
        db.commit()


class ReviewCreate(BaseModel):
    order_id: int
    restaurant_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class AppReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


@router.get("/reviews/by-order")
async def get_review_by_order(order_id: int, user_id: int = Depends(require_user_id), db: Session = Depends(get_db)) -> dict:
    r = db.query(DBReview).filter(DBReview.order_id == order_id, DBReview.user_id == user_id, DBReview.is_deleted == False).first()
    return {"exists": r is not None, "review": {
        "id": r.id, "order_id": r.order_id, "restaurant_id": r.restaurant_id, "user_id": r.user_id,
        "rating": r.rating, "comment": r.comment, "created_at": r.created_at
    } if r else None}


@router.post("/reviews")
async def create_review(payload: ReviewCreate, user_id: int = Depends(require_user_id), db: Session = Depends(get_db)) -> dict:
    # user must own the order
    o = db.query(DBOrder).filter(DBOrder.id == payload.order_id, DBOrder.user_id == user_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="order_not_found")
    # prevent duplicate
    existed = db.query(DBReview).filter(DBReview.order_id == payload.order_id, DBReview.user_id == user_id, DBReview.is_deleted == False).first()
    if existed:
        raise HTTPException(status_code=400, detail="already_reviewed")
    rv = DBReview(
        order_id=payload.order_id,
        restaurant_id=payload.restaurant_id,
        user_id=user_id,
        rating=payload.rating,
        comment=payload.comment or "",
    )
    db.add(rv)
    db.commit()
    db.refresh(rv)
    
    # Обновляем рейтинг ресторана
    update_restaurant_rating(payload.restaurant_id, db)
    
    return {"status": "ok", "id": rv.id}


@router.get("/app-reviews")
async def get_app_reviews(db: Session = Depends(get_db)) -> dict:
    """Получить все отзывы о приложении"""
    reviews = db.query(DBAppReview).filter(DBAppReview.is_deleted == False).order_by(DBAppReview.created_at.desc()).all()
    return {
        "reviews": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at
            } for r in reviews
        ]
    }


@router.post("/app-reviews")
async def create_app_review(payload: AppReviewCreate, user_id: int = Depends(require_user_id), db: Session = Depends(get_db)) -> dict:
    """Создать отзыв о приложении"""
    # Проверяем, не оставлял ли пользователь уже отзыв
    existed = db.query(DBAppReview).filter(DBAppReview.user_id == user_id, DBAppReview.is_deleted == False).first()
    if existed:
        raise HTTPException(status_code=400, detail="already_reviewed")
    
    review = DBAppReview(
        user_id=user_id,
        rating=payload.rating,
        comment=payload.comment or "",
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {"status": "ok", "id": review.id}


@router.get("/app-reviews/my")
async def get_my_app_review(user_id: int = Depends(require_user_id), db: Session = Depends(get_db)) -> dict:
    """Получить отзыв пользователя о приложении"""
    review = db.query(DBAppReview).filter(DBAppReview.user_id == user_id, DBAppReview.is_deleted == False).first()
    return {
        "exists": review is not None,
        "review": {
            "id": review.id,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at
        } if review else None
    }


@router.get("/reviews/restaurant/{restaurant_id}")
async def get_restaurant_reviews(restaurant_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить все отзывы о ресторане"""
    reviews = db.query(DBReview).filter(
        DBReview.restaurant_id == restaurant_id,
        DBReview.is_deleted == False
    ).order_by(DBReview.created_at.desc()).all()
    
    # Получаем средний рейтинг
    avg_rating = db.query(func.avg(DBReview.rating)).filter(
        DBReview.restaurant_id == restaurant_id,
        DBReview.is_deleted == False
    ).scalar()
    
    # Оптимизированный запрос - получаем всех пользователей одним запросом
    user_ids = [r.user_id for r in reviews]
    users = db.query(DBUser).filter(DBUser.id.in_(user_ids)).all()
    users_map = {u.id: u for u in users}
    
    # Получаем все элементы заказов одним запросом
    order_ids = [r.order_id for r in reviews]
    order_items = db.query(DBOrderItem).filter(DBOrderItem.order_id.in_(order_ids)).all()
    order_items_map = {}
    for item in order_items:
        if item.order_id not in order_items_map:
            order_items_map[item.order_id] = []
        order_items_map[item.order_id].append(item)
    
    # Формируем данные отзывов
    reviews_data = []
    for r in reviews:
        # Получаем имя пользователя из кэша
        user = users_map.get(r.user_id)
        user_name = user.name if user and user.name else "Аноним"
        
        # Получаем состав заказа из кэша
        items = order_items_map.get(r.order_id, [])
        ordered_items = ", ".join([f"{item.name} x{item.qty}" for item in items]) if items else None
        
        reviews_data.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": user_name,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at,
            "ordered_items": ordered_items
        })
    
    return {
        "reviews": reviews_data,
        "average_rating": round(avg_rating or 0.0, 1),
        "total_reviews": len(reviews)
    }

