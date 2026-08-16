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


