#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция: Добавление поля legal_address в таблицу restaurants
"""
import sqlite3
import sys
import os

def find_db():
    """Находит файл базы данных с таблицей restaurants"""
    possible_paths = [
        'data.db',
        'app.db',
        'app/data.db',
        '../data.db',
        '../app.db'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            # Проверяем, есть ли в этой БД таблица restaurants
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='restaurants'")
                if cursor.fetchone():
                    conn.close()
                    return path
                conn.close()
            except:
                pass
    return None

def main():
    # Настраиваем вывод для Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    db_path = find_db()
    if not db_path:
        print("❌ База данных не найдена!")
        print("Искали в:", ['app.db', 'data.db', 'app/data.db', '../app.db', '../data.db'])
        sys.exit(1)
    
    print(f"📦 Найдена база данных: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли поле legal_address
        cursor.execute("PRAGMA table_info(restaurants)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'legal_address' in columns:
            print("✅ Поле legal_address уже существует в таблице restaurants")
            conn.close()
            return
        
        print("➕ Добавляем поле legal_address в таблицу restaurants...")
        cursor.execute("ALTER TABLE restaurants ADD COLUMN legal_address TEXT DEFAULT ''")
        conn.commit()
        
        print("✅ Поле legal_address успешно добавлено!")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

