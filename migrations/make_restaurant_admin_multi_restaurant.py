#!/usr/bin/env python3
"""
Миграция для поддержки нескольких ресторанов для одного админа.
Изменяет структуру таблицы restaurant_admins: делает составной primary key (user_id, restaurant_id)
вместо только user_id.
"""
import sqlite3
import os

def migrate():
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
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли таблица
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='restaurant_admins'
        """)
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("📝 Table restaurant_admins doesn't exist. Creating it with correct structure...")
            cursor.execute("""
                CREATE TABLE restaurant_admins (
                    user_id INTEGER NOT NULL,
                    restaurant_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, restaurant_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
                )
            """)
            print("✅ Table created successfully")
            conn.commit()
            return
        
        # Таблица существует, проверяем структуру
        cursor.execute("PRAGMA table_info(restaurant_admins)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Current table structure: {', '.join(column_names)}")
        
        if "user_id" not in column_names or "restaurant_id" not in column_names:
            print("❌ Table restaurant_admins has unexpected structure")
            print(f"   Expected columns: user_id, restaurant_id")
            print(f"   Found columns: {', '.join(column_names)}")
            return
        
        # Проверяем, есть ли уже составной primary key
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='restaurant_admins'")
        table_sql = cursor.fetchone()
        table_sql_str = table_sql[0] if table_sql else ""
        
        # Проверяем, есть ли составной ключ (оба поля в PRIMARY KEY)
        has_composite_key = (
            "PRIMARY KEY" in table_sql_str and 
            "user_id" in table_sql_str and 
            "restaurant_id" in table_sql_str and
            table_sql_str.find("PRIMARY KEY") < table_sql_str.find("restaurant_id")
        )
        
        if has_composite_key:
            print("✅ Table already has composite primary key (user_id, restaurant_id)")
            return
        
        print("🔄 Migrating restaurant_admins table to support multiple restaurants per admin...")
        
        # Сохраняем существующие данные
        try:
            cursor.execute("SELECT user_id, restaurant_id FROM restaurant_admins")
            existing_data = cursor.fetchall()
            print(f"📊 Found {len(existing_data)} existing admin records")
        except sqlite3.OperationalError as e:
            print(f"⚠️  Could not read existing data: {e}")
            existing_data = []
        
        # Создаем новую таблицу с составным ключом
        cursor.execute("""
            CREATE TABLE restaurant_admins_new (
                user_id INTEGER NOT NULL,
                restaurant_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, restaurant_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
        """)
        
        # Копируем данные (удаляем дубликаты, если есть)
        if existing_data:
            unique_data = list(set(existing_data))
            try:
                cursor.executemany(
                    "INSERT INTO restaurant_admins_new (user_id, restaurant_id) VALUES (?, ?)",
                    unique_data
                )
                print(f"✅ Copied {len(unique_data)} unique records to new table")
            except sqlite3.IntegrityError as e:
                print(f"⚠️  Some records were skipped due to duplicates: {e}")
        
        # Удаляем старую таблицу
        cursor.execute("DROP TABLE restaurant_admins")
        
        # Переименовываем новую таблицу
        cursor.execute("ALTER TABLE restaurant_admins_new RENAME TO restaurant_admins")
        
        print("✅ Migration completed successfully")
        
    except sqlite3.OperationalError as e:
        error_msg = str(e).lower()
        if "already exists" in error_msg or "duplicate" in error_msg:
            print("✅ Migration already applied or table structure is correct")
        else:
            print(f"❌ Error during migration: {e}")
            print(f"   Error type: {type(e).__name__}")
            raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    migrate()

