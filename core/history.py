"""
Tarjima tarixini ma'lumotlar bazasiga saqlash va o'qish uchun qulay funksiyalar.
Bot ham, veb-sahifa ham shu modulni ishlatadi — SQL so'rovlari faqat shu
yerda yoziladi, boshqa joyda takrorlanmaydi.
"""
from .db import get_session
from .models import TranslationHistory


def save_translation(source, user_identifier, original_text, translated_text,
                      direction, engine, is_voice=False):
    """Bitta tarjimani ma'lumotlar bazasiga yozadi."""
    session = get_session()
    try:
        record = TranslationHistory(
            source=source,
            user_identifier=str(user_identifier),
            original_text=original_text,
            translated_text=translated_text,
            direction=direction,
            engine=engine,
            is_voice=1 if is_voice else 0,
        )
        session.add(record)
        session.commit()
    finally:
        session.close()


