#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция: добавление поля cuisine в таблицу restaurants
"""
import sqlite3
import os
import sys

# Устанавливаем UTF-8 для вывода в Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def find_db():
    """Ищет файл базы данных с таблицей restaurants"""
    possible_paths = [
        'data.db',  # Приоритет data.db (используется по умолчанию)
        'app.db',
        'app/data.db',
        '../data.db',
        '../app.db',
    ]
    
    # Сначала проверяем, в каком файле есть таблица restaurants
    for path in possible_paths:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='restaurants'")
                if cursor.fetchone():
                    conn.close()
                    return path
                conn.close()
            except Exception:
                pass
    
    # Если не нашли таблицу, возвращаем первый существующий файл
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def main():
    db_path = find_db()
    if not db_path:
        print("❌ Файл базы данных не найден")
        sys.exit(1)
    
    print(f"📦 Используется БД: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли таблица restaurants
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='restaurants'")
        if not cursor.fetchone():
            print("❌ Таблица restaurants не найдена в этом файле БД")
            print("💡 Проверьте, что используете правильный файл базы данных")
            # Показываем список всех таблиц для отладки
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            if tables:
                print(f"📋 Найденные таблицы: {', '.join([t[0] for t in tables])}")
            sys.exit(1)
        
        # Проверяем, есть ли уже поле cuisine
        cursor.execute("PRAGMA table_info(restaurants)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'cuisine' in columns:
            print("✅ Поле cuisine уже существует в таблице restaurants")
        else:
            print("➕ Добавляем поле cuisine в таблицу restaurants...")
            cursor.execute("ALTER TABLE restaurants ADD COLUMN cuisine VARCHAR(200) DEFAULT ''")
            conn.commit()
            print("✅ Поле cuisine успешно добавлено")
        
        conn.close()
        print("✅ Миграция завершена успешно")
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"❌ Ошибка при выполнении миграции: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

