import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

# sqlite pragmas for better defaults and performance
connect_args = {
    "check_same_thread": False,
    "timeout": 20,
    "isolation_level": None  # Автокоммит для лучшей производительности
} if DATABASE_URL.startswith("sqlite") else {}

def _optimize_sqlite_on_connect(dbapi_con, con_record):
    """Оптимизация SQLite для лучшей производительности"""
    try:
        cursor = dbapi_con.cursor()
        # Включаем foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        # WAL режим для лучшей производительности при чтении/записи
        cursor.execute("PRAGMA journal_mode=WAL")
        # Нормальная синхронизация (быстрее чем FULL)
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Увеличиваем кэш до 10MB
        cursor.execute("PRAGMA cache_size=10000")
        # Временные таблицы в памяти
        cursor.execute("PRAGMA temp_store=MEMORY")
        # MMAP для больших файлов (256MB)
        cursor.execute("PRAGMA mmap_size=268435456")
        # Оптимизация для запросов
        cursor.execute("PRAGMA optimize")
        cursor.close()
    except Exception:
        pass

engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    future=True, 
    connect_args=connect_args,
    # Увеличиваем pool size для лучшей производительности
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

if DATABASE_URL.startswith("sqlite"):
    try:
        from sqlalchemy import event
        event.listen(engine, "connect", _optimize_sqlite_on_connect)
    except Exception:
        pass
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    future=True,
)
Base = declarative_base()


def get_session() -> Session:
    return SessionLocal()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

