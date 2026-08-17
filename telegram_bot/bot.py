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


