"""
Ma'lumotlar bazasi ulanishi (SQLAlchemy orqali).

PostgreSQL'ga ulanish uchun .env faylida DATABASE_URL sozlanishi kerak, masalan:
    DATABASE_URL=postgresql://foydalanuvchi:parol@localhost:5432/logistika_tarjimon

Agar DATABASE_URL sozlanmagan bo'lsa, mahalliy sinov uchun avtomatik
ravishda SQLite fayliga (fallback.db) o'tadi — bu development'da PostgreSQL
o'rnatilmagan bo'lsa ham loyihani ishga tushirish imkonini beradi.
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    # Zaxira variant — PostgreSQL sozlanmagan bo'lsa, mahalliy SQLite ishlatiladi.
    DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'fallback.db'}"

# SQLite uchun maxsus parametr kerak (bir nechta thread'dan foydalanish uchun)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    """Barcha jadvallarni (agar mavjud bo'lmasa) yaratadi. Dastur ishga tushganda chaqiriladi."""
    from . import models  # noqa: F401 — modellarni ro'yxatdan o'tkazish uchun import qilinadi
    Base.metadata.create_all(bind=engine)


def get_session():
    """Yangi database session ochadi. Ishlatib bo'lgach, albatta session.close() chaqiring."""
    return SessionLocal()