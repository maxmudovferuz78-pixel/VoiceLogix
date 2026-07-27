"""
Ovozli tarjima logikasi.

Ishlash tartibi:
1. Kiruvchi ovoz (o'zbekcha yoki inglizcha, farqi yo'q) Gemini'ga
   to'g'ridan-to'g'ri audio sifatida yuboriladi. Gemini qaysi tilda
   gapirilganini aniqlaydi VA darhol boshqa tilga tarjima qiladi —
   alohida "speech-to-text" bosqichi shart emas.
2. Natijadagi matn ovozga aylantiriladi:
   - Agar natija INGLIZCHA bo'lsa -> Deepgram (tabiiy amerikacha ovoz)
   - Agar natija O'ZBEKCHA bo'lsa -> Edge-TTS (bepul, chunki Deepgram
     o'zbek tilini hali qo'llab-quvvatlamaydi)
"""
import base64
import json
import os

import asyncio
import edge_tts
import requests

from .glossary import glossary_as_prompt_text

GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"

# Deepgram'ning bir nechta amerikacha ovozlari — birini tanlang:
#   aura-2-thalia-en  -> ayol ovozi, iliq va tabiiy
#   aura-2-orion-en   -> erkak ovozi, ishonchli va professional
#   aura-2-luna-en    -> ayol ovozi, yosh va tiniq
DEEPGRAM_VOICE_MODEL = "aura-2-orion-en"

# Edge-TTS'ning o'zbekcha ovozlari — birini tanlang:
#   uz-UZ-MadinaNeural -> ayol ovozi
#   uz-UZ-SardorNeural -> erkak ovozi
UZBEK_VOICE = "uz-UZ-SardorNeural"

VOICE_SYSTEM_PROMPT = f"""Sen logistika (freight/trucking) sohasida ishlaydigan professional tarjimonsan.
Senga ovozli xabar beriladi — bu xabar O'ZBEK yoki INGLIZ tilida bo'lishi mumkin.

VAZIFANG:
1. Ovozdagi tilni aniqla (o'zbekcha bo'lsa "uz", inglizcha bo'lsa "en").
2. Xabarni boshqa tilga tarjima qil (o'zbekcha bo'lsa inglizchaga, inglizcha bo'lsa o'zbekchaga).
3. Ingliz tiliga tarjima qilganda tabiiy, ravon amerikacha uslubda yoz.
4. Javobni QISQA va TABIIY yoz — ortiqcha so'z qo'shma, so'zma-so'z tarjima qilma.
5. Quyidagi logistika atamalaridan foydalanib, kontekstga mos tarjima qil:

{glossary_as_prompt_text()}

NAMUNALAR:
"Yukni qachon olib ketasiz?" -> "When are you picking up the load?"
"Kutish haqi qancha bo'ladi?" -> "How much is the detention fee?"
"What's the rate for this load?" -> "Bu yuk uchun tarif qancha?"

JAVOBNI FAQAT quyidagi JSON formatida qaytar, boshqa hech qanday matn yozma:
{{"detected_language": "uz" yoki "en", "translated_text": "tarjima matni shu yerda"}}
"""


def _get_gemini_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY topilmadi. .env faylida GEMINI_API_KEY=... sozlang."
        )
    return api_key


def transcribe_and_translate_audio(audio_bytes, mime_type="audio/ogg"):
    """
    Ovoz baytlarini (masalan Telegram'dan kelgan .ogg fayl) Gemini'ga yuborib,
    tilni aniqlaydi va tarjima qiladi.

    Returns:
        dict: {"detected_language": "uz"|"en", "translated_text": str}
    """
    api_key = _get_gemini_key()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "systemInstruction": {"parts": [{"text": VOICE_SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
                    {"text": "Shu ovozli xabarni tinglab, yuqoridagi ko'rsatmaga rioya qil."},
                ],
            }
        ],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300},
    }

    response = requests.post(GEMINI_URL, params={"key": api_key}, json=payload, timeout=25)
    response.raise_for_status()
    data = response.json()
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Gemini ba'zan ```json ... ``` ko'rinishida qaytarishi mumkin — tozalaymiz
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(cleaned)

    return {
        "detected_language": parsed["detected_language"],
        "translated_text": parsed["translated_text"],
    }


def _synthesize_english_deepgram(text):
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPGRAM_API_KEY topilmadi. .env faylida DEEPGRAM_API_KEY=... sozlang."
        )

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    params = {"model": DEEPGRAM_VOICE_MODEL, "encoding": "mp3"}
    response = requests.post(
        DEEPGRAM_TTS_URL, params=params, headers=headers,
        json={"text": text}, timeout=30,
    )
    response.raise_for_status()
    return response.content  # mp3 bayt oqimi


def _synthesize_uzbek_edge_tts(text):
    async def _generate():
        communicate = edge_tts.Communicate(text, UZBEK_VOICE, rate="+8%")
        audio_chunks = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.extend(chunk["data"])
        return bytes(audio_chunks)

    return asyncio.run(_generate())


def synthesize_speech(text, target_lang):
    """
    Matnni ovozga aylantiradi.

    Args:
        text: ovozga aylantiriladigan matn
        target_lang: "en" (Deepgram, amerikacha) yoki "uz" (Edge-TTS, bepul)

    Returns:
        bytes: mp3 formatidagi audio
    """
    if target_lang == "en":
        return _synthesize_english_deepgram(text)
    return _synthesize_uzbek_edge_tts(text)