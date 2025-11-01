from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
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


# ========== SEARCH API ==========

@router.get("/search")
async def search(
    q: str = Query(..., description="Поисковый запрос"),
    type: Optional[str] = Query(None, description="Тип: restaurants, dishes, или все (не указывать)"),
    with_promotions: Optional[bool] = Query(None, description="Только с акциями"),
    db: Session = Depends(get_db)
):
    """
    Поиск ресторанов и блюд (в стиле Яндекс.Еда)
    Возвращает рестораны с их блюдами, сгруппированные по ресторанам
    """
    search_term = q.strip()
    if not search_term:
        return {
            "restaurants": [],
            "total": 0
        }
    
    results = {
        "restaurants": [],
        "total": 0
    }
    
    # Поиск ресторанов (case-insensitive, работает с кириллицей)
    # Используем фильтрацию в Python для корректной работы с кириллицей
    search_term_lower = search_term.lower()
    
    # Получаем все активные рестораны
    restaurant_query = db.query(DBRestaurant).filter(DBRestaurant.is_enabled == True)
    
    # Фильтр по акциям для ресторанов
    restaurants_with_promos_ids = None
    if with_promotions:
        restaurants_with_promos = db.query(DBPromotion.restaurant_id).filter(
            DBPromotion.is_active == True,
            DBPromotion.restaurant_id.isnot(None)
        ).distinct().all()
        restaurants_with_promos_ids = {r.restaurant_id for r in restaurants_with_promos}
        if not restaurants_with_promos_ids:
            restaurants_with_promos_ids = {-1}  # Пустое множество для фильтрации
    
    all_restaurants = restaurant_query.all()
    
    # Фильтруем в Python для корректной работы с кириллицей
    restaurants = []
    for r in all_restaurants:
        if with_promotions and r.id not in restaurants_with_promos_ids:
            continue
        
        name_match = search_term_lower in r.name.lower() if r.name else False
        desc_match = search_term_lower in r.description.lower() if r.description else False
        
        if name_match or desc_match:
            restaurants.append(r)
    
    # Поиск блюд (case-insensitive, работает с кириллицей)
    # Получаем все доступные блюда
    dish_query = db.query(DBDish).filter(
        DBDish.is_available == True
    ).join(DBRestaurant, DBDish.restaurant_id == DBRestaurant.id).filter(
        DBRestaurant.is_enabled == True
    )
    
    # Фильтр по акциям для блюд
    if with_promotions and restaurants_with_promos_ids:
        dish_query = dish_query.filter(
            DBDish.restaurant_id.in_(list(restaurants_with_promos_ids))
        )
    
    all_dishes = dish_query.all()
    
    # Фильтруем в Python для корректной работы с кириллицей
    dishes = []
    for d in all_dishes:
        name_match = search_term_lower in d.name.lower() if d.name else False
        desc_match = search_term_lower in d.description.lower() if d.description else False
        
        if name_match or desc_match:
            dishes.append(d)
    
    # Группируем блюда по ресторанам
    restaurant_dict = {}
    
    # Добавляем рестораны, найденные по названию
    for restaurant in restaurants:
        if restaurant.id not in restaurant_dict:
            rating = get_restaurant_rating(restaurant.id, db)
            restaurant_dict[restaurant.id] = {
                "id": restaurant.id,
                "name": restaurant.name,
                "rating": rating,
                "delivery_time_minutes": restaurant.delivery_time_minutes,
                "delivery_fee": restaurant.delivery_fee,
                "delivery_min_sum": restaurant.delivery_min_sum,
                "image": restaurant.image,
                "dishes": []
            }
    
    # Добавляем блюда в соответствующие рестораны
    for dish in dishes:
        if dish.restaurant_id not in restaurant_dict:
            restaurant = db.query(DBRestaurant).filter(DBRestaurant.id == dish.restaurant_id).first()
            if restaurant:
                rating = get_restaurant_rating(restaurant.id, db)
                restaurant_dict[dish.restaurant_id] = {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "rating": rating,
                    "delivery_time_minutes": restaurant.delivery_time_minutes,
                    "delivery_fee": restaurant.delivery_fee,
                    "delivery_min_sum": restaurant.delivery_min_sum,
                    "image": restaurant.image,
                    "dishes": []
                }
        
        restaurant_dict[dish.restaurant_id]["dishes"].append({
            "id": dish.id,
            "name": dish.name,
            "price": dish.price,
            "image": dish.image,
            "description": dish.description
        })
    
    # Для ресторанов, найденных по названию, но без блюд в результатах поиска,
    # показываем несколько популярных блюд из этого ресторана (как в Яндекс.Еда)
    restaurant_ids_with_dishes = {dish.restaurant_id for dish in dishes}
    
    for restaurant in restaurants:
        if restaurant.id not in restaurant_ids_with_dishes:
            # Ресторан найден по названию, но нет блюд в результатах поиска
            # Показываем несколько популярных блюд из этого ресторана
            popular_dishes = db.query(DBDish).filter(
                DBDish.restaurant_id == restaurant.id,
                DBDish.is_available == True
            ).limit(5).all()  # Показываем до 5 блюд
            
            if restaurant.id in restaurant_dict:
                restaurant_dict[restaurant.id]["dishes"] = [
                    {
                        "id": d.id,
                        "name": d.name,
                        "price": d.price,
                        "image": d.image,
                        "description": d.description
                    }
                    for d in popular_dishes
                ]
    
    # Фильтруем по типу результата
    restaurant_list = list(restaurant_dict.values())
    
    if type == "restaurants":
        # Только рестораны (показываем их блюда тоже)
        restaurant_list = [
            r for r in restaurant_list 
            if r["id"] in [res.id for res in restaurants]
        ]
    elif type == "dishes":
        # Только рестораны с найденными блюдами
        restaurant_list = [
            r for r in restaurant_list 
            if len(r["dishes"]) > 0
        ]
    
    results["restaurants"] = restaurant_list
    results["total"] = sum(len(r["dishes"]) for r in restaurant_list) + len([r for r in restaurant_list if len(r["dishes"]) == 0])
    
    return results