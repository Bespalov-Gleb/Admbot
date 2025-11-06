#!/usr/bin/env python3
"""
Простой скрипт для проверки здоровья бота.
Можно запустить через cron каждые 5 минут:
*/5 * * * * /path/to/venv/bin/python /path/to/bot/healthcheck.py
"""
import os
import httpx
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("SUPER_ADMIN_IDS", "").split(",")[0]  # Первый админ


async def check_bot_health():
    """Проверяет доступность Telegram API"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
            )
            if response.status_code == 200:
                print(f"[{datetime.now()}] ✅ Bot is healthy")
                return True
            else:
                print(f"[{datetime.now()}] ❌ Bot API returned {response.status_code}")
                return False
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Bot health check failed: {e}")
        await send_alert(f"⚠️ Bot health check failed: {e}")
        return False


async def send_alert(message: str):
    """Отправляет алерт админу"""
    if not ADMIN_CHAT_ID or not BOT_TOKEN:
        return
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": ADMIN_CHAT_ID,
                    "text": message
                }
            )
    except Exception as e:
        print(f"Failed to send alert: {e}")


if __name__ == "__main__":
    asyncio.run(check_bot_health())

