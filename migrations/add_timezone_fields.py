#!/usr/bin/env python3
"""
Миграция для добавления полей timezone в таблицы users и restaurants
"""

import sqlite3
import os

def run_migration():
    """Добавляет поля timezone в таблицы users и restaurants"""
    
    db_path = "data.db"
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Выполняем миграцию: добавление полей timezone...")
        
        # Проверяем, существует ли уже колонка timezone в таблице users
        cursor.execute("PRAGMA table_info(users)")
        users_columns = [column[1] for column in cursor.fetchall()]
        
        if 'timezone' not in users_columns:
            print("📝 Добавляем поле timezone в таблицу users...")
            cursor.execute("ALTER TABLE users ADD COLUMN timezone VARCHAR(32) DEFAULT 'UTC+9'")
            print("✅ Поле timezone добавлено в таблицу users")
        else:
            print("ℹ️  Поле timezone уже существует в таблице users")
        
        # Проверяем, существует ли уже колонка timezone в таблице restaurants
        cursor.execute("PRAGMA table_info(restaurants)")
        restaurants_columns = [column[1] for column in cursor.fetchall()]
        
        if 'timezone' not in restaurants_columns:
            print("📝 Добавляем поле timezone в таблицу restaurants...")
            cursor.execute("ALTER TABLE restaurants ADD COLUMN timezone VARCHAR(32) DEFAULT 'UTC+9'")
            print("✅ Поле timezone добавлено в таблицу restaurants")
        else:
            print("ℹ️  Поле timezone уже существует в таблице restaurants")
        
        # Обновляем существующие записи
        print("🔄 Обновляем существующие записи...")
        cursor.execute("UPDATE users SET timezone = 'UTC+9' WHERE timezone IS NULL")
        cursor.execute("UPDATE restaurants SET timezone = 'UTC+9' WHERE timezone IS NULL")
        
        conn.commit()
        print("✅ Миграция успешно выполнена!")
        
        # Проверяем результат
        cursor.execute("SELECT COUNT(*) FROM users WHERE timezone IS NOT NULL")
        users_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM restaurants WHERE timezone IS NOT NULL")
        restaurants_count = cursor.fetchone()[0]
        
        print(f"📊 Результат:")
        print(f"   - Пользователей с timezone: {users_count}")
        print(f"   - Ресторанов с timezone: {restaurants_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("=== Миграция: добавление полей timezone ===")
    success = run_migration()
    if success:
        print("\n🎉 Миграция завершена успешно!")
        print("Теперь можно использовать timezone в приложении.")
    else:
        print("\n💥 Миграция завершилась с ошибкой!")
        exit(1)