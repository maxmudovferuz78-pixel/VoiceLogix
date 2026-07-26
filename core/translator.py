"""
Asosiy tarjima logikasi. Ikki bosqichli yondashuv:

1. Agar GEMINI_API_KEY sozlangan bo'lsa — Gemini AI orqali tarjima qilinadi.
   Bu ancha aniqroq, chunki logistika lug'atini "kontekst" sifatida tushunib,
   tabiiy va to'g'ri tarjima qila oladi. Gemini'ning bepul tarifi (free tier)
   yetarli darajada so'rov limitiga ega.

2. Agar Gemini ishlamasa (kalit yo'q yoki xatolik) — avtomatik ravishda
   bepul Google Tarjimon (deep-translator) ishlatiladi, zaxira sifatida.

Web ilova ham, Telegram bot ham shu modulni ishlatadi — mantiq bitta joyda
saqlanadi, ikki marta yozilmaydi.
"""
import os
import requests
from deep_translator import GoogleTranslator

from .glossary import LOGISTICS_GLOSSARY, glossary_as_prompt_text

GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_PROMPT = f"""Sen logistika (freight/trucking) sohasida ishlaydigan professional tarjimonsan.
O'zbek tilidan ingliz tiliga (yoki aksincha) tarjima qilasan.

QOIDALAR:
1. Faqat tarjimani qaytar — hech qanday izoh, tushuntirish, qo'shimcha matn yozma.
2. Ingliz tiliga tarjima qilganda, tabiiy, ravon amerikacha uslubda yoz — so'zma-so'z
   tarjima emas, xuddi tug'ilganidan amerikalik odam gapirgandek tabiiy chiqishi kerak.
3. Quyidagi logistika atamalaridan foydalanib, kontekstga mos tarjima qil:

{glossary_as_prompt_text()}

4. Agar matn savol bo'lsa, tarjimasi ham savol shaklida bo'lsin.
5. Rasmiy-professional ohangda yoz (bu ish suhbati, do'stona chat emas)."""


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


def _translate_with_gemini(text, direction):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None  # kalit yo'q — zaxira variantga o'tiladi

    if direction == "uz_to_en":
        instruction = f"Quyidagi o'zbekcha matnni ingliz tiliga tarjima qil:\n\n{text}"
    else:
        instruction = f"Quyidagi inglizcha matnni o'zbek tiliga tarjima qil:\n\n{text}"

    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": instruction}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512},
    }

    try:
        response = requests.post(
            GEMINI_URL, params={"key": api_key}, json=payload, timeout=20
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        # Har qanday muammoda (internet, limit, formatdagi xatolik) jim
        # ravishda zaxira variantga o'tamiz — foydalanuvchi xatolik ko'rmaydi.
        return None


def _apply_glossary_uz_to_en(uz_text, en_translation):
    """Zaxira variant (Google Tarjimon) uchun atamalarni tekshirib, eslatma qo'shadi."""
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


def _translate_with_google_free(text, direction):
    if direction == "uz_to_en":
        translated = GoogleTranslator(source="uz", target="en").translate(text)
        translated = _apply_glossary_uz_to_en(text, translated)
    else:
        translated = GoogleTranslator(source="en", target="uz").translate(text)
    return translated


def translate(text, direction=None):
    """
    Matnni tarjima qiladi. Avval Gemini AI'ni sinaydi, muvaffaqiyatsiz
    bo'lsa bepul Google Tarjimonga o'tadi.

    Args:
        text: tarjima qilinadigan matn
        direction: "uz_to_en", "en_to_uz" yoki None (avtomatik aniqlanadi)

    Returns:
        dict: {"translated_text": str, "direction": str, "engine": str}
    """
    if not text or not text.strip():
        return {"translated_text": "", "direction": direction or "uz_to_en", "engine": "none"}

    if direction is None:
        direction = detect_direction(text)

    gemini_result = _translate_with_gemini(text, direction)
    if gemini_result:
        return {"translated_text": gemini_result, "direction": direction, "engine": "gemini"}

    fallback_result = _translate_with_google_free(text, direction)
    return {"translated_text": fallback_result, "direction": direction, "engine": "google_free"}
