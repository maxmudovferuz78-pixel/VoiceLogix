"""
Asosiy tarjima logikasi. Bu modul BEPUL Google Tarjimon kutubxonasi
(deep-translator) orqali o'zbekcha <-> inglizcha tarjima qiladi, so'ng
bizning logistika lug'atimizdan foydalanib, atamalarni to'g'rilaydi.

Hech qanday API kalit yoki to'lov kerak emas.

Web ilova ham, Telegram bot ham shu modulni ishlatadi — mantiq bitta joyda
saqlanadi, ikki marta yozilmaydi.
"""
from deep_translator import GoogleTranslator

from .glossary import LOGISTICS_GLOSSARY


def detect_direction(text):
    """
    Juda oddiy til aniqlash: agar matnda o'zbekcha harflar yoki so'zlar
    ko'p bo'lsa — o'zbekcha deb hisoblanadi. 100% aniq emas, lekin MVP
    uchun yetarli.
    """
    uzbek_markers = ["o'", "g'", " va ", " bilan ", " uchun ", " qancha", " qachon", " bormi", " nima"]
    text_lower = text.lower()
    score = sum(1 for marker in uzbek_markers if marker in text_lower)
    return "uz_to_en" if score > 0 else "en_to_uz"


def _apply_glossary_uz_to_en(uz_text, en_translation):
    """
    Google Tarjimon ba'zan logistika atamalarini noto'g'ri tarjima qiladi.
    Agar asl matnda bizning lug'atimizdagi atama bo'lsa, tarjimada to'g'ri
    inglizcha atama borligini tekshiramiz; bo'lmasa, izoh sifatida qo'shamiz.
    """
    notes = []
    uz_lower = uz_text.lower()
    for uz_term, (en_term, note) in LOGISTICS_GLOSSARY.items():
        if uz_term.split(" / ")[0] in uz_lower:
            correct_word = en_term.split(" / ")[0].split(" (")[0]
            if correct_word.lower() not in en_translation.lower():
                notes.append(f"{uz_term} = {en_term}")
    if notes:
        en_translation += "\n\n[Atama eslatmasi: " + "; ".join(notes) + "]"
    return en_translation


def translate(text, direction=None):
    """
    Matnni tarjima qiladi.

    Args:
        text: tarjima qilinadigan matn
        direction: "uz_to_en", "en_to_uz" yoki None (avtomatik aniqlanadi)

    Returns:
        dict: {"translated_text": str, "direction": str}
    """
    if not text or not text.strip():
        return {"translated_text": "", "direction": direction or "uz_to_en"}

    if direction is None:
        direction = detect_direction(text)

    if direction == "uz_to_en":
        translated = GoogleTranslator(source="uz", target="en").translate(text)
        translated = _apply_glossary_uz_to_en(text, translated)
    else:
        translated = GoogleTranslator(source="en", target="uz").translate(text)

    return {"translated_text": translated, "direction": direction}
