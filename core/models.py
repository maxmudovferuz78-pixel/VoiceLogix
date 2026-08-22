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

    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    direction = Column(String(10), nullable=False)   # "uz_to_en" yoki "en_to_uz"
    engine = Column(String(20), nullable=False)       # "gemini", "google_free", "voice"
    is_voice = Column(Integer, default=0)              # 0 = matn, 1 = ovozli xabar

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_history_user", "source", "user_identifier"),
    )

    def __repr__(self):
        return f"<TranslationHistory {self.id}: {self.original_text[:30]!r}>"