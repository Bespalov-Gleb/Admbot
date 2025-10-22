from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import Collection as DBCollection, CollectionItem as DBCollectionItem, Restaurant as DBRestaurant, Dish as DBDish, Review as DBReview, Promotion as DBPromotion
import os

router = APIRouter()


def get_restaurant_rating(restaurant_id: int, db: Session) -> float:
    """Получить актуальный рейтинг ресторана на основе отзывов"""
    avg_rating = db.query(func.avg(DBReview.rating)).filter(
        DBReview.restaurant_id == restaurant_id,
        DBReview.is_deleted == False
    ).scalar()
    return round(avg_rating or 0.0, 1)


@router.get("/collections")
async def get_public_collections(db: Session = Depends(get_db)) -> List[dict]:
    """Получить все активные подборки для главной страницы"""
    collections = db.query(DBCollection).filter(DBCollection.is_enabled == True).order_by(DBCollection.sort_order, DBCollection.id).all()
    result = []
    
    for collection in collections:
        items = db.query(DBCollectionItem).filter(
            DBCollectionItem.collection_id == collection.id,
            DBCollectionItem.is_enabled == True
        ).order_by(DBCollectionItem.sort_order, DBCollectionItem.id).all()
        
        collection_items = []
        for item in items:
            # Получаем дополнительную информацию о ресторане или блюде
            item_data = {
                "id": item.id,
                "type": item.item_type,
                "item_id": item.item_id,
                "title": item.title,
                "subtitle": item.subtitle,
                "image": item.image,
                "link_url": item.link_url
            }
            
            if item.item_type == "restaurant":
                restaurant = db.query(DBRestaurant).filter(DBRestaurant.id == item.item_id).first()
                if restaurant:
                    # Получаем актуальный рейтинг из отзывов
                    actual_rating = get_restaurant_rating(restaurant.id, db)
                    print(f"Restaurant {restaurant.name} (ID: {restaurant.id}) - rating: {actual_rating}")
                    item_data["restaurant"] = {
                        "id": restaurant.id,
                        "name": restaurant.name,
                        "rating": actual_rating,
                        "delivery_min_sum": restaurant.delivery_min_sum,
                        "delivery_fee": restaurant.delivery_fee,
                        "delivery_time_minutes": restaurant.delivery_time_minutes
                    }
            elif item.item_type == "dish":
                dish = db.query(DBDish).filter(DBDish.id == item.item_id).first()
                if dish:
                    # Получаем информацию о ресторане для блюда
                    restaurant = db.query(DBRestaurant).filter(DBRestaurant.id == dish.restaurant_id).first()
                    item_data["dish"] = {
                        "id": dish.id,
                        "name": dish.name,
                        "price": dish.price,
                        "description": dish.description
                    }
                    if restaurant:
                        # Получаем актуальный рейтинг из отзывов
                        actual_rating = get_restaurant_rating(restaurant.id, db)
                        print(f"Restaurant {restaurant.name} (ID: {restaurant.id}) for dish - rating: {actual_rating}")
                        item_data["restaurant"] = {
                            "id": restaurant.id,
                            "name": restaurant.name,
                            "rating": actual_rating,
                            "delivery_min_sum": restaurant.delivery_min_sum,
                            "delivery_fee": restaurant.delivery_fee,
                            "delivery_time_minutes": restaurant.delivery_time_minutes
                        }
            
            collection_items.append(item_data)
        
        result.append({
            "id": collection.id,
            "name": collection.name,
            "description": collection.description,
            "image": collection.image,
            "items": collection_items
        })
    
    return result


# ========== PROMOTIONS API (PUBLIC) ==========

@router.get("/promotions")
async def get_public_promotions(db: Session = Depends(get_db)):
    """Получить список всех активных акций (публичный доступ)"""
    
    promotions = db.query(DBPromotion).filter(
        DBPromotion.is_active == True,
        DBPromotion.restaurant_id.isnot(None)  # Только акции с рестораном
    ).order_by(DBPromotion.created_at.desc()).all()
    
    result = []
    for promotion in promotions:
        restaurant_name = None
        restaurant_image = None
        if promotion.restaurant_id:
            restaurant = db.query(DBRestaurant).filter(DBRestaurant.id == promotion.restaurant_id).first()
            restaurant_name = restaurant.name if restaurant else None
            restaurant_image = restaurant.image if restaurant else None
        
        result.append({
            "id": promotion.id,
            "name": promotion.name,
            "description": promotion.description,
            "image": promotion.image,
            "restaurant_id": promotion.restaurant_id,
            "restaurant_name": restaurant_name,
            "restaurant_image": restaurant_image,
            "created_at": promotion.created_at.isoformat()
        })
    
    return result


# ========== DOCUMENTS API ==========

def encode_filename_for_header(filename: str) -> str:
    """Кодирует имя файла для использования в HTTP заголовках"""
    import urllib.parse
    return f"filename*=UTF-8''{urllib.parse.quote(filename)}"

@router.get("/documents/user-agreement")
async def download_user_agreement():
    """Скачать пользовательское соглашение"""
    file_path = "webapp/static/Пользовательское-соглашение-ВкусАпп.pdf"
    try:
        if os.path.exists(file_path):
            print(f"DEBUG: Serving user agreement from {file_path}")
            filename = "Пользовательское соглашение ВкусАпп.pdf"
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; {encode_filename_for_header(filename)}",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        else:
            print(f"DEBUG: User agreement file not found at {file_path}")
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Файл не найден")
    except Exception as e:
        print(f"DEBUG: Error serving user agreement: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")


@router.get("/documents/privacy-policy")
async def download_privacy_policy():
    """Скачать политику конфиденциальности"""
    file_path = "webapp/static/Политика-конфиденциальности-ВкусАпп.pdf"
    try:
        if os.path.exists(file_path):
            print(f"DEBUG: Serving privacy policy from {file_path}")
            filename = "Политика конфиденциальности ВкусАпп.pdf"
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; {encode_filename_for_header(filename)}",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        else:
            print(f"DEBUG: Privacy policy file not found at {file_path}")
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Файл не найден")
    except Exception as e:
        print(f"DEBUG: Error serving privacy policy: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")


@router.get("/documents/restaurant-offer")
async def download_restaurant_offer():
    """Скачать оферту для ресторанов"""
    file_path = "webapp/static/Оферта-ВкусАпп.pdf"
    try:
        if os.path.exists(file_path):
            print(f"DEBUG: Serving restaurant offer from {file_path}")
            filename = "Оферта ВкусАпп.pdf"
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; {encode_filename_for_header(filename)}",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        else:
            print(f"DEBUG: Restaurant offer file not found at {file_path}")
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Файл не найден")
    except Exception as e:
        print(f"DEBUG: Error serving restaurant offer: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}") 