#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция: создание таблицы restaurant_info_blocks
"""

import os
import sqlite3
import sys


def find_db() -> str | None:
    """
    Ищет файл базы данных с таблицей restaurants.
    Логика аналогична другим миграциям (cuisine / legal_address).
    """
    possible_paths = [
        "data.db",
        "app.db",
        "app/data.db",
        "../data.db",
        "../app.db",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='restaurants'"
                )
                if cursor.fetchone():
                    conn.close()
                    return path
                conn.close()
            except Exception:
                pass
    return None


def main() -> None:
    # Настраиваем вывод для Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    db_path = find_db()
    if not db_path:
        print("❌ База данных не найдена или в ней нет таблицы restaurants")
        sys.exit(1)

    print(f"📦 Найдена база данных: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Проверяем, существует ли уже таблица restaurant_info_blocks
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='restaurant_info_blocks'"
        )
        if cursor.fetchone():
            print("✅ Таблица restaurant_info_blocks уже существует")
            conn.close()
            return

        print("➕ Создаём таблицу restaurant_info_blocks...")
        cursor.execute(
            """
            CREATE TABLE restaurant_info_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL,
                title VARCHAR(128) NOT NULL,
                description TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                is_enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
            """
        )

        # Индексы, как в модели
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_restaurant_info_blocks_restaurant_id "
            "ON restaurant_info_blocks (restaurant_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_restaurant_info_blocks_sort "
            "ON restaurant_info_blocks (restaurant_id, sort_order)"
        )

        conn.commit()
        print("✅ Таблица restaurant_info_blocks успешно создана")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Ошибка при выполнении миграции: {e}")
        sys.exit(1)
    finally:
        conn.close()
        print("✅ Миграция завершена")


if __name__ == "__main__":
    main()


