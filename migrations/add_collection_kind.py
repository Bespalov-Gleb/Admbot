"""
Миграция для добавления поля kind в таблицу collections
"""

import sqlite3
import os

def migrate():
    db_path = "data.db"
    
    if not os.path.exists(db_path):
        print("База данных не найдена")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли уже поле kind
        cursor.execute("PRAGMA table_info(collections)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'kind' not in columns:
            # Добавляем поле kind
            cursor.execute("ALTER TABLE collections ADD COLUMN kind VARCHAR(32) DEFAULT 'restaurants'")
            print("Поле 'kind' добавлено в таблицу collections")
        else:
            print("Поле 'kind' уже существует в таблице collections")
        
        conn.commit()
        print("Миграция выполнена успешно")
        
    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()