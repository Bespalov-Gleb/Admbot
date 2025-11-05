import os
import httpx
from dotenv import load_dotenv
from app.logging_config import get_logger
from aiogram import Bot


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHANNEL_ID = os.getenv("ADMIN_CHANNEL_ID", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
SUPPORT_TG_URL = os.getenv("SUPPORT_TG_URL", "https://t.me/support")
logger = get_logger("telegram")

# Создаем объект бота для рассылки
bot = Bot(BOT_TOKEN) if BOT_TOKEN else None


async def send_admin_message(text: str) -> None:
    if not BOT_TOKEN or not ADMIN_CHANNEL_ID:
        logger.warning("admin_message: missing token or channel")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_CHANNEL_ID, "text": text}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json=payload)
        except Exception as exc:
            logger.exception("admin_message: exception: %s", repr(exc))
            return


async def send_user_message(chat_id: int, text: str, button_text: str | None = None, button_url: str | None = None) -> bool:
    if not BOT_TOKEN or not chat_id:
        logger.warning("user_message: missing token or chat_id")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text}
    if button_text and button_url:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": button_text, "web_app": {"url": button_url}}]]
        }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, json=payload)
            ok = 200 <= resp.status_code < 300
            if not ok:
                logger.error(
                    "user_message: non-200 response", extra={
                        "status": resp.status_code, "body": resp.text, "chat_id": chat_id, "url": button_url
                    }
                )
            return ok
        except Exception as exc:
            logger.exception("user_message: exception: %s", repr(exc))
            return False


async def notify_user_order_modified(chat_id: int, url: str, text: str | None = None) -> None:
    if not BOT_TOKEN or not chat_id:
        return
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text or "Заказ изменён рестораном. Нажмите, чтобы открыть текущий заказ.",
        "reply_markup": {"inline_keyboard": [[{"text": "Открыть текущий заказ", "web_app": {"url": url}}]]},
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(api, json=payload)
        except Exception:
            return


async def notify_user_order_cancelled(chat_id: int, restaurant_name: str, reason: str | None = None) -> None:
    if not BOT_TOKEN or not chat_id:
        return
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    reason_text = f"\n\nПричина отмены: {reason}" if reason else ""
    text = f"Ресторан \"{restaurant_name}\" отменил заказ.{reason_text}"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(api, json=payload)
        except Exception:
            return


async def notify_user_order_accepted(chat_id: int, url: str, restaurant_name: str, eta_minutes: int, delivery_type: str = "delivery") -> None:
    if not BOT_TOKEN or not chat_id:
        return
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Формируем текст в зависимости от типа доставки
    if delivery_type == "pickup":
        text = f"Ресторан \"{restaurant_name}\" принял Ваш заказ на самовывоз."
    else:
        text = f"Ресторан \"{restaurant_name}\" принял Ваш заказ.  Время доставки - {eta_minutes} мин."
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": [[{"text": "Открыть текущий заказ", "web_app": {"url": url}}]]},
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(api, json=payload)
        except Exception:
            return


async def notify_user_order_delivered(chat_id: int, order_id: int, restaurant_name: str) -> None:
    """Отправляет уведомление клиенту о доставке заказа с предложением оценки"""
    if not BOT_TOKEN or not chat_id:
        return
    
    review_url = f"{WEBAPP_URL}/static/order.html?id={order_id}&show_review=1"
    
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = f"🎉 Ваш заказ из ресторана \"{restaurant_name}\" доставлен!\n\nПожалуйста, оцените качество обслуживания и оставьте отзыв о ресторане."
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "⭐ Оценить ресторан", "web_app": {"url": review_url}}
            ]]
        },
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(api, json=payload)
        except Exception as exc:
            logger.exception("notify_user_order_delivered: exception: %s", repr(exc))
            return


async def notify_restaurant_admins(restaurant_id: int, message: str, button_text: str | None = None, button_url: str | None = None) -> None:
    """Отправляет уведомление всем админам конкретного ресторана"""
    if not BOT_TOKEN:
        return
    
    # Получаем список админов ресторана из базы данных
    from app.db import get_session
    from app.models import RestaurantAdmin
    
    try:
        db = get_session()
        admin_rows = db.query(RestaurantAdmin).filter(RestaurantAdmin.restaurant_id == restaurant_id).all()
        
        if not admin_rows:
            logger.warning(f"No restaurant admins found for restaurant_id={restaurant_id}")
            return
        
        api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        for admin in admin_rows:
            payload = {
                "chat_id": admin.user_id,
                "text": message
            }
            
            if button_text and button_url:
                # Добавляем uid админа в URL
                admin_url = button_url
                if '?' in button_url:
                    admin_url += f"&uid={admin.user_id}"
                else:
                    admin_url += f"?uid={admin.user_id}"
                
                payload["reply_markup"] = {
                    "inline_keyboard": [[
                        {"text": button_text, "web_app": {"url": admin_url}}
                    ]]
                }
            
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    resp = await client.post(api, json=payload)
                    if resp.status_code == 200:
                        logger.info(f"Notification sent to restaurant admin {admin.user_id} for restaurant {restaurant_id}")
                    else:
                        logger.warning(f"Failed to send notification to admin {admin.user_id}: {resp.status_code}")
                except Exception as exc:
                    logger.exception(f"Error sending notification to admin {admin.user_id}: {exc}")
                    
    except Exception as exc:
        logger.exception(f"Error in notify_restaurant_admins: {exc}")
    finally:
        if 'db' in locals():
            db.close()


async def resolve_username_to_user_id(username: str) -> int | None:
    """Разрешает username в user_id через Telegram Bot API"""
    if not BOT_TOKEN:
        logger.warning("resolve_username: missing bot token")
        return None
    
    # Убираем @ если есть
    clean_username = username.lstrip('@')
    
    # Сначала ищем в нашей базе данных
    from app.store import get_user_by_username
    db_user_id = get_user_by_username(clean_username)
    if db_user_id:
        logger.info("resolve_username: found user %s in database with id %d", clean_username, db_user_id)
        return db_user_id
    
    # Пробуем метод getChat (работает с публичными каналами/группами)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    payload = {"chat_id": f"@{clean_username}"}
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") and data.get("result"):
                    return data["result"]["id"]
        except Exception:
            pass
    
    # Если getChat не сработал, пробуем метод getUpdates для поиска пользователя
    # Это работает только если пользователь недавно взаимодействовал с ботом
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        resp = await client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    if "message" in update:
                        user = update["message"].get("from")
                        if user and user.get("username") == clean_username:
                            return user["id"]
                    elif "callback_query" in update:
                        user = update["callback_query"].get("from")
                        if user and user.get("username") == clean_username:
                            return user["id"]
    except Exception:
        pass
    
    # Если ничего не сработало, возвращаем None
    # Пользователь должен сначала взаимодействовать с ботом
    logger.warning("resolve_username: failed to resolve %s. User must interact with bot first.", username)
    return None


async def notify_restaurant_comment(order_id: int, restaurant_id: int, comment: str, user_id: int) -> None:
    """Отправить уведомление ресторану о комментарии от клиента"""
    if not BOT_TOKEN:
        logger.warning("notify_restaurant_comment: missing bot token")
        return
    
    try:
        # Получаем список администраторов ресторана
        from app.db import get_session
        from app.models import RestaurantAdmin
        
        with get_session() as db:
            admins = db.query(RestaurantAdmin).filter(RestaurantAdmin.restaurant_id == restaurant_id).all()
            
            if not admins:
                logger.warning(f"No admins found for restaurant {restaurant_id}")
                return
            
            # Формируем сообщение
            message = f"💬 <b>Новый комментарий к заказу №{order_id}</b>\n\n"
            message += f"<b>Комментарий:</b>\n{comment}\n\n"
            message += f"<b>Заказ:</b> №{order_id}\n"
            message += f"<b>Клиент:</b> ID {user_id}"
            
            # Отправляем каждому администратору ресторана
            for admin in admins:
                try:
                    await send_user_message(admin.user_id, message)
                    logger.info(f"Comment notification sent to restaurant admin {admin.user_id} for order {order_id}")
                except Exception as exc:
                    logger.error(f"Failed to send comment notification to admin {admin.user_id}: {exc}")
                    
    except Exception as exc:
        logger.exception(f"Failed to notify restaurant about comment for order {order_id}: {exc}")


