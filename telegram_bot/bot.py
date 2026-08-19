"""
Logistika Tarjimon — Telegram bot.

Ishga tushirish:
    cd logistics-translator
    python telegram_bot/bot.py

Kerakli narsa: loyiha tub papkasida (.env faylida) TELEGRAM_BOT_TOKEN
va GEMINI_API_KEY sozlangan bo'lishi kerak.
"""
import io
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# --- Yo'llarni sozlash: "core" modulini import qila olishimiz uchun ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)

from core import translate, READY_PHRASES, init_db, save_translation, get_recent_history
from core.voice import transcribe_and_translate_audio, synthesize_speech

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _remember(user_id, original, translated, direction="uz_to_en", engine="gemini", is_voice=False):
    """Tarjimani ma'lumotlar bazasiga (PostgreSQL/SQLite) yozadi."""
    try:
        save_translation(
            source="telegram",
            user_identifier=user_id,
            original_text=original,
            translated_text=translated,
            direction=direction,
            engine=engine,
            is_voice=is_voice,
        )
    except Exception:
        logger.exception("Tarixni bazaga yozishda xatolik")


WELCOME_MESSAGE = (
    "👋 Assalomu alaykum! Men *Logistika Tarjimon* botiman.\n\n"
    "Menga o'zbekcha yoki inglizcha matn YOKI ovozli xabar yuboring — "
    "men uni logistika atamalarini hisobga olib tarjima qilib beraman.\n"
    "Ovozli xabar yuborsangiz, tarjimani ham ovozda eshitasiz!\n\n"
    "Masalan:\n"
    "🔹 \"Yukni qachon olib ketasiz?\"\n"
    "🔹 \"What's the detention rate?\"\n\n"
    "Buyruqlar:\n"
    "/phrases — tayyor iboralar (tugma bosib yuborish)\n"
    "/history — oxirgi tarjimalaringiz\n"
    "/help — yordam"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Shunchaki menga matn yozing (o'zbekcha yoki inglizcha) — "
        "men avtomatik tilni aniqlab, tarjima qilib beraman."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        result = translate(user_text)
        translated_text = result["translated_text"]
        engine = result["engine"]

        _remember(
            update.effective_user.id, user_text, translated_text,
            direction=result["direction"], engine=engine, is_voice=False,
        )

        direction_label = (
            "🇺🇿 → 🇺🇸" if result["direction"] == "uz_to_en" else "🇺🇸 → 🇺🇿"
        )
        engine_label = "Gemini AI" if engine == "gemini" else "Google Tarjimon (zaxira)"

        reply = f"{direction_label}\n\n{translated_text}\n\n_({engine_label})_"
        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception:
        logger.exception("Tarjima qilishda xatolik yuz berdi")
        await update.message.reply_text(
            "⚠️ Kechirasiz, tarjima qilishda xatolik yuz berdi. "
            "Birozdan so'ng qayta urinib ko'ring."
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_voice")

    try:
        voice_file = await update.message.voice.get_file()
        audio_bytes = bytes(await voice_file.download_as_bytearray())

        result = transcribe_and_translate_audio(audio_bytes, mime_type="audio/ogg")
        detected_lang = result["detected_language"]
        translated_text = result["translated_text"]
        target_lang = "en" if detected_lang == "uz" else "uz"

        direction = "uz_to_en" if detected_lang == "uz" else "en_to_uz"
        _remember(
            update.effective_user.id, "(ovozli xabar)", translated_text,
            direction=direction, engine="gemini_voice", is_voice=True,
        )

        audio_out = synthesize_speech(translated_text, target_lang)

        direction_label = "🇺🇿 → 🇺🇸" if detected_lang == "uz" else "🇺🇸 → 🇺🇿"
        await update.message.reply_text(f"{direction_label}\n\n{translated_text}")

        audio_stream = io.BytesIO(audio_out)
        audio_stream.name = "tarjima.mp3"
        await update.message.reply_audio(audio=audio_stream)

    except Exception:
        logger.exception("Ovozli xabarni qayta ishlashda xatolik yuz berdi")
        await update.message.reply_text(
            "⚠️ Kechirasiz, ovozli xabarni qayta ishlashda xatolik yuz berdi. "
            "Birozdan so'ng qayta urinib ko'ring."
        )


async def phrases_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(short_label, callback_data=f"phrase:{i}")]
        for i, (full_text, short_label) in enumerate(READY_PHRASES)
    ]
    await update.message.reply_text(
        "Kerakli iborani tanlang — men darhol tarjima qilib beraman:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def phrase_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        index = int(query.data.split(":")[1])
        phrase_text = READY_PHRASES[index][0]
    except (IndexError, ValueError):
        await query.message.reply_text("⚠️ Ibora topilmadi, qaytadan /phrases yozing.")
        return

    result = translate(phrase_text)
    translated_text = result["translated_text"]
    _remember(
        query.from_user.id, phrase_text, translated_text,
        direction=result["direction"], engine=result["engine"], is_voice=False,
    )

    await query.message.reply_text(f"🇺🇿 {phrase_text}\n🇺🇸 {translated_text}")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        history = get_recent_history(source="telegram", user_identifier=user_id, limit=5)
    except Exception:
        logger.exception("Tarixni bazadan o'qishda xatolik")
        await update.message.reply_text(
            "⚠️ Tarixni yuklashda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."
        )
        return

