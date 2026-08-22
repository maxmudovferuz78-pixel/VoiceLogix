"""
Ma'lumotlar bazasi modellari (jadval tuzilmalari).
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, Index

from .db import Base


class TranslationHistory(Base):
    """
    Har bir tarjima (matn yoki ovoz) shu jadvalga yoziladi.
    Telegram bot ham, veb-sahifa ham shu bitta jadvaldan foydalanadi.
    """
    __tablename__ = "translation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Kim tarjima qilgani: Telegram foydalanuvchisi bo'lsa uning ID'si,
    # veb-sahifa foydalanuvchisi bo'lsa brauzer sessiya ID'si.
    source = Column(String(20), nullable=False)          # "telegram" yoki "web"
    user_identifier = Column(String(64), nullable=False)  # telegram_user_id yoki session_key
