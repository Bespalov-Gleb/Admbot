#!/usr/bin/env python3
"""
Миграция для добавления поля cutlery_count в таблицу orders
"""

import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data.db')
    
    if not os.path.exists(db_path):
        print(f"База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Сначала посмотрим, какие таблицы есть в базе данных
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Таблицы в базе данных:", [table[0] for table in tables])
        
        # Проверяем, существует ли таблица orders
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("❌ Таблица orders не найдена. Доступные таблицы:", [table[0] for table in tables])
            return
        
        # Проверяем, существует ли уже поле cutlery_count
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'cutlery_count' not in columns:
            print("Добавляем поле cutlery_count в таблицу orders...")
            cursor.execute("ALTER TABLE orders ADD COLUMN cutlery_count INTEGER DEFAULT 0")
            conn.commit()
            print("✅ Поле cutlery_count успешно добавлено")
        else:
            print("✅ Поле cutlery_count уже существует")
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()