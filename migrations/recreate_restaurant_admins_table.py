#!/usr/bin/env python3
"""
Альтернативный скрипт для пересоздания таблицы restaurant_admins.
Используйте этот скрипт, если основная миграция не работает.
ВНИМАНИЕ: Этот скрипт удалит все данные из таблицы restaurant_admins!
"""
import sqlite3
import os

def recreate_table():
    # Проверяем оба возможных пути к базе данных
    db_paths = ["app.db", "data.db", "app/data.db"]
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print(f"❌ Database file not found. Checked: {', '.join(db_paths)}")
        return
    
    print(f"📁 Using database: {db_path}")
    print("⚠️  WARNING: This will DELETE all data from restaurant_admins table!")
    
    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Cancelled")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Удаляем старую таблицу
        cursor.execute("DROP TABLE IF EXISTS restaurant_admins")
        print("✅ Old table dropped")
        
        # Создаем новую таблицу с правильной структурой
        cursor.execute("""
            CREATE TABLE restaurant_admins (
                user_id INTEGER NOT NULL,
                restaurant_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, restaurant_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
        """)
        print("✅ New table created with composite primary key")
        
        conn.commit()
        print("✅ Table recreated successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    recreate_table()

